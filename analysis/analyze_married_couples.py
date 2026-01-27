#!/usr/bin/env python3
"""
Married couples analysis between civi_staging and replica_profiles.
Identifies married couples (Couple relationship type) in CiVi and matches them
to VH users via email-based matching.

Usage:
    python analyze_married_couples.py
"""

import pandas as pd
from sqlalchemy import text
from collections import Counter
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import csv
import sys
import os

from common import (
    MatchType,
    get_database_engines,
    normalize_email,
    extract_civi_email_data,
    extract_civi_contact_data,
    extract_replica_profile_data,
    build_civi_email_lookup,
    build_civi_contact_lookup,
)


# CiVi Relationship Type ID for "Couple" (married)
COUPLE_RELATIONSHIP_TYPE_ID = 69


class CoupleMatchStatus(Enum):
    """Status of VH matching for a married couple."""
    BOTH_MATCHED = "both_matched"        # Both spouses matched to VH users
    ONLY_A_MATCHED = "only_a_matched"    # Only contact_a matched to VH
    ONLY_B_MATCHED = "only_b_matched"    # Only contact_b matched to VH
    NEITHER_MATCHED = "neither_matched"  # Neither spouse matched to VH


@dataclass
class CiviCouple:
    """Represents a married couple from CiVi."""
    relationship_id: int
    contact_id_a: int
    contact_id_b: int
    first_name_a: Optional[str]
    last_name_a: Optional[str]
    email_a: Optional[str]
    first_name_b: Optional[str]
    last_name_b: Optional[str]
    email_b: Optional[str]
    is_active: bool
    start_date: Optional[str]
    end_date: Optional[str]


@dataclass
class CoupleMatch:
    """Represents a married couple with VH matching info."""
    # CiVi relationship info
    relationship_id: int
    contact_id_a: int
    contact_id_b: int
    civi_first_name_a: Optional[str]
    civi_last_name_a: Optional[str]
    civi_email_a: Optional[str]
    civi_first_name_b: Optional[str]
    civi_last_name_b: Optional[str]
    civi_email_b: Optional[str]
    
    # VH match info for contact_a
    vh_user_id_a: Optional[str]
    vh_email_matched_a: Optional[str]
    vh_match_type_a: Optional[MatchType]
    vh_first_name_a: Optional[str]
    vh_last_name_a: Optional[str]
    vh_primary_email_a: Optional[str]
    
    # VH match info for contact_b
    vh_user_id_b: Optional[str]
    vh_email_matched_b: Optional[str]
    vh_match_type_b: Optional[MatchType]
    vh_first_name_b: Optional[str]
    vh_last_name_b: Optional[str]
    vh_primary_email_b: Optional[str]
    
    # Overall status
    match_status: CoupleMatchStatus


@dataclass
class CoupleConflict:
    """Represents a conflict when a CiVi contact matches multiple VH users."""
    relationship_id: int
    contact_id: int  # Which contact has the conflict (A or B)
    is_contact_a: bool  # True if contact_a, False if contact_b
    civi_first_name: Optional[str]
    civi_last_name: Optional[str]
    civi_email: Optional[str]
    # List of VH matches for this contact
    vh_matches: List[Tuple[str, str, MatchType, str, str, str]]  # (user_id, email_matched, match_type, first_name, last_name, primary_email)


def extract_civi_couples(engine) -> pd.DataFrame:
    """Extract married couples (Couple relationship) from CiVi.
    
    Returns DataFrame with relationship and contact info for both spouses.
    """
    print("Extracting married couples from CiVi...")
    
    query = text(f"""
        SELECT 
            r.id as relationship_id,
            r.contact_id_a,
            r.contact_id_b,
            r.is_active,
            r.start_date,
            r.end_date,
            ca.first_name as first_name_a,
            ca.last_name as last_name_a,
            ca.is_deleted as is_deleted_a,
            cb.first_name as first_name_b,
            cb.last_name as last_name_b,
            cb.is_deleted as is_deleted_b,
            (SELECT email FROM staging1pay_testbb_top_civi.civicrm_email 
             WHERE contact_id = r.contact_id_a AND is_primary = 1 LIMIT 1) as email_a,
            (SELECT email FROM staging1pay_testbb_top_civi.civicrm_email 
             WHERE contact_id = r.contact_id_b AND is_primary = 1 LIMIT 1) as email_b
        FROM staging1pay_testbb_top_civi.civicrm_relationship r
        JOIN staging1pay_testbb_top_civi.civicrm_contact ca ON r.contact_id_a = ca.id
        JOIN staging1pay_testbb_top_civi.civicrm_contact cb ON r.contact_id_b = cb.id
        WHERE r.relationship_type_id = {COUPLE_RELATIONSHIP_TYPE_ID}
        AND r.is_active = 1
        AND ca.is_deleted = 0
        AND cb.is_deleted = 0
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        print(f"  Extracted {len(df)} active married couples")
        return df
    except Exception as e:
        print(f"  Error extracting couples data: {e}")
        return pd.DataFrame()


def build_vh_email_lookup(replica_profiles_df: pd.DataFrame) -> Dict[str, List[Tuple[str, bool, pd.Series]]]:
    """Build VH email lookup: normalized_email -> list of (user_id, is_primary, full_row)"""
    vh_email_lookup: Dict[str, List[Tuple[str, bool, pd.Series]]] = {}
    
    for _, row in replica_profiles_df.iterrows():
        user_id = row['user_id']
        
        if pd.notna(row['primary_email']):
            email_norm = normalize_email(row['primary_email'])
            if email_norm:
                if email_norm not in vh_email_lookup:
                    vh_email_lookup[email_norm] = []
                vh_email_lookup[email_norm].append((user_id, True, row))
        
        if pd.notna(row['alternate_email_1']):
            email_norm = normalize_email(row['alternate_email_1'])
            if email_norm:
                if email_norm not in vh_email_lookup:
                    vh_email_lookup[email_norm] = []
                vh_email_lookup[email_norm].append((user_id, False, row))
        
        if pd.notna(row['alternate_email_2']):
            email_norm = normalize_email(row['alternate_email_2'])
            if email_norm:
                if email_norm not in vh_email_lookup:
                    vh_email_lookup[email_norm] = []
                vh_email_lookup[email_norm].append((user_id, False, row))
    
    return vh_email_lookup


def find_vh_matches_for_civi_contact(
    contact_id: int,
    civi_emails_df: pd.DataFrame,
    vh_email_lookup: Dict[str, List[Tuple[str, bool, pd.Series]]]
) -> Dict[str, Tuple[str, MatchType, pd.Series]]:
    """Find VH users matching a CiVi contact by email.
    
    Returns: user_id -> (email_matched, match_type, vh_row)
    """
    # Get all emails for this contact
    contact_emails = civi_emails_df[civi_emails_df['contact_id'] == contact_id]
    
    # user_id -> best match info
    user_matches: Dict[str, Tuple[str, MatchType, pd.Series]] = {}
    
    for _, email_row in contact_emails.iterrows():
        email_norm = normalize_email(email_row['email'])
        if not email_norm or email_norm not in vh_email_lookup:
            continue
        
        civi_is_primary = email_row['is_primary'] == 1
        
        for vh_user_id, vh_is_primary, vh_row in vh_email_lookup[email_norm]:
            # Determine match type
            if civi_is_primary and vh_is_primary:
                match_type = MatchType.PRIMARY_TO_PRIMARY
            elif civi_is_primary and not vh_is_primary:
                match_type = MatchType.PRIMARY_TO_ALT
            elif not civi_is_primary and vh_is_primary:
                match_type = MatchType.ALT_TO_PRIMARY
            else:
                match_type = MatchType.ALT_TO_ALT
            
            # Keep the best match type for this user
            if vh_user_id not in user_matches:
                user_matches[vh_user_id] = (email_norm, match_type, vh_row)
            else:
                existing_match_type = user_matches[vh_user_id][1]
                if match_type.priority < existing_match_type.priority:
                    user_matches[vh_user_id] = (email_norm, match_type, vh_row)
    
    return user_matches


def analyze_married_couples(
    couples_df: pd.DataFrame,
    civi_emails_df: pd.DataFrame,
    replica_profiles_df: pd.DataFrame
) -> Tuple[List[CoupleMatch], List[CoupleConflict]]:
    """Analyze married couples and match them to VH users.
    
    Auto-merge: When a CiVi contact matches multiple VH users, if they are the same
    spouse pair (both in the relationship), we auto-merge. Otherwise, it's a conflict.
    
    Returns:
        Tuple of (couple_matches, conflicts)
    """
    print("Analyzing married couples with VH matching...")
    
    # Build VH email lookup
    vh_email_lookup = build_vh_email_lookup(replica_profiles_df)
    
    couple_matches: List[CoupleMatch] = []
    conflicts: List[CoupleConflict] = []
    
    stats = {
        'total_couples': len(couples_df),
        'both_matched': 0,
        'only_a_matched': 0,
        'only_b_matched': 0,
        'neither_matched': 0,
        'conflicts_a': 0,
        'conflicts_b': 0,
        'auto_merged_a': 0,
        'auto_merged_b': 0,
    }
    
    for _, couple_row in couples_df.iterrows():
        relationship_id = couple_row['relationship_id']
        contact_id_a = couple_row['contact_id_a']
        contact_id_b = couple_row['contact_id_b']
        
        # Find VH matches for each spouse
        matches_a = find_vh_matches_for_civi_contact(contact_id_a, civi_emails_df, vh_email_lookup)
        matches_b = find_vh_matches_for_civi_contact(contact_id_b, civi_emails_df, vh_email_lookup)
        
        # Check for conflicts - a conflict is when a contact matches multiple VH users
        # that are NOT the spouse in this relationship
        
        # For contact A: conflict if matches multiple VH users and they're not all the spouse
        conflict_a = False
        best_match_a = None
        if len(matches_a) > 1:
            # Check if one of the matches is the spouse (contact_b's VH match)
            spouse_vh_ids = set(matches_b.keys()) if matches_b else set()
            non_spouse_matches = {uid: m for uid, m in matches_a.items() if uid not in spouse_vh_ids}
            
            if len(non_spouse_matches) > 1:
                # True conflict - multiple non-spouse matches
                conflict_a = True
                stats['conflicts_a'] += 1
                conflicts.append(CoupleConflict(
                    relationship_id=relationship_id,
                    contact_id=contact_id_a,
                    is_contact_a=True,
                    civi_first_name=couple_row['first_name_a'] if pd.notna(couple_row['first_name_a']) else None,
                    civi_last_name=couple_row['last_name_a'] if pd.notna(couple_row['last_name_a']) else None,
                    civi_email=couple_row['email_a'] if pd.notna(couple_row['email_a']) else None,
                    vh_matches=[
                        (uid, m[0], m[1], 
                         m[2]['first_name_latin'] if pd.notna(m[2]['first_name_latin']) else None,
                         m[2]['last_name_latin'] if pd.notna(m[2]['last_name_latin']) else None,
                         m[2]['primary_email'] if pd.notna(m[2]['primary_email']) else None)
                        for uid, m in matches_a.items()
                    ]
                ))
            else:
                # Auto-merge: pick best match (prefer non-spouse if available, then best priority)
                stats['auto_merged_a'] += 1
                if non_spouse_matches:
                    best_uid = min(non_spouse_matches.keys(), 
                                  key=lambda uid: (non_spouse_matches[uid][1].priority, uid))
                    best_match_a = (best_uid, *non_spouse_matches[best_uid])
                else:
                    best_uid = min(matches_a.keys(), 
                                  key=lambda uid: (matches_a[uid][1].priority, uid))
                    best_match_a = (best_uid, *matches_a[best_uid])
        elif len(matches_a) == 1:
            best_uid = list(matches_a.keys())[0]
            best_match_a = (best_uid, *matches_a[best_uid])
        
        # Same logic for contact B
        conflict_b = False
        best_match_b = None
        if len(matches_b) > 1:
            spouse_vh_ids = set(matches_a.keys()) if matches_a else set()
            non_spouse_matches = {uid: m for uid, m in matches_b.items() if uid not in spouse_vh_ids}
            
            if len(non_spouse_matches) > 1:
                conflict_b = True
                stats['conflicts_b'] += 1
                conflicts.append(CoupleConflict(
                    relationship_id=relationship_id,
                    contact_id=contact_id_b,
                    is_contact_a=False,
                    civi_first_name=couple_row['first_name_b'] if pd.notna(couple_row['first_name_b']) else None,
                    civi_last_name=couple_row['last_name_b'] if pd.notna(couple_row['last_name_b']) else None,
                    civi_email=couple_row['email_b'] if pd.notna(couple_row['email_b']) else None,
                    vh_matches=[
                        (uid, m[0], m[1],
                         m[2]['first_name_latin'] if pd.notna(m[2]['first_name_latin']) else None,
                         m[2]['last_name_latin'] if pd.notna(m[2]['last_name_latin']) else None,
                         m[2]['primary_email'] if pd.notna(m[2]['primary_email']) else None)
                        for uid, m in matches_b.items()
                    ]
                ))
            else:
                stats['auto_merged_b'] += 1
                if non_spouse_matches:
                    best_uid = min(non_spouse_matches.keys(),
                                  key=lambda uid: (non_spouse_matches[uid][1].priority, uid))
                    best_match_b = (best_uid, *non_spouse_matches[best_uid])
                else:
                    best_uid = min(matches_b.keys(),
                                  key=lambda uid: (matches_b[uid][1].priority, uid))
                    best_match_b = (best_uid, *matches_b[best_uid])
        elif len(matches_b) == 1:
            best_uid = list(matches_b.keys())[0]
            best_match_b = (best_uid, *matches_b[best_uid])
        
        # Determine match status
        if conflict_a or conflict_b:
            # Skip creating CoupleMatch if there are conflicts - they're in conflicts list
            continue
        
        a_matched = best_match_a is not None
        b_matched = best_match_b is not None
        
        if a_matched and b_matched:
            match_status = CoupleMatchStatus.BOTH_MATCHED
            stats['both_matched'] += 1
        elif a_matched:
            match_status = CoupleMatchStatus.ONLY_A_MATCHED
            stats['only_a_matched'] += 1
        elif b_matched:
            match_status = CoupleMatchStatus.ONLY_B_MATCHED
            stats['only_b_matched'] += 1
        else:
            match_status = CoupleMatchStatus.NEITHER_MATCHED
            stats['neither_matched'] += 1
        
        # Create CoupleMatch
        couple_match = CoupleMatch(
            relationship_id=relationship_id,
            contact_id_a=contact_id_a,
            contact_id_b=contact_id_b,
            civi_first_name_a=couple_row['first_name_a'] if pd.notna(couple_row['first_name_a']) else None,
            civi_last_name_a=couple_row['last_name_a'] if pd.notna(couple_row['last_name_a']) else None,
            civi_email_a=couple_row['email_a'] if pd.notna(couple_row['email_a']) else None,
            civi_first_name_b=couple_row['first_name_b'] if pd.notna(couple_row['first_name_b']) else None,
            civi_last_name_b=couple_row['last_name_b'] if pd.notna(couple_row['last_name_b']) else None,
            civi_email_b=couple_row['email_b'] if pd.notna(couple_row['email_b']) else None,
            # VH match info for A
            vh_user_id_a=best_match_a[0] if best_match_a else None,
            vh_email_matched_a=best_match_a[1] if best_match_a else None,
            vh_match_type_a=best_match_a[2] if best_match_a else None,
            vh_first_name_a=best_match_a[3]['first_name_latin'] if best_match_a and pd.notna(best_match_a[3]['first_name_latin']) else None,
            vh_last_name_a=best_match_a[3]['last_name_latin'] if best_match_a and pd.notna(best_match_a[3]['last_name_latin']) else None,
            vh_primary_email_a=best_match_a[3]['primary_email'] if best_match_a and pd.notna(best_match_a[3]['primary_email']) else None,
            # VH match info for B
            vh_user_id_b=best_match_b[0] if best_match_b else None,
            vh_email_matched_b=best_match_b[1] if best_match_b else None,
            vh_match_type_b=best_match_b[2] if best_match_b else None,
            vh_first_name_b=best_match_b[3]['first_name_latin'] if best_match_b and pd.notna(best_match_b[3]['first_name_latin']) else None,
            vh_last_name_b=best_match_b[3]['last_name_latin'] if best_match_b and pd.notna(best_match_b[3]['last_name_latin']) else None,
            vh_primary_email_b=best_match_b[3]['primary_email'] if best_match_b and pd.notna(best_match_b[3]['primary_email']) else None,
            match_status=match_status
        )
        couple_matches.append(couple_match)
    
    print(f"  Total couples: {stats['total_couples']:,}")
    print(f"  - Both matched: {stats['both_matched']:,}")
    print(f"  - Only A matched: {stats['only_a_matched']:,}")
    print(f"  - Only B matched: {stats['only_b_matched']:,}")
    print(f"  - Neither matched: {stats['neither_matched']:,}")
    print(f"  - Auto-merged (A): {stats['auto_merged_a']:,}")
    print(f"  - Auto-merged (B): {stats['auto_merged_b']:,}")
    print(f"  - Conflicts (A): {stats['conflicts_a']:,}")
    print(f"  - Conflicts (B): {stats['conflicts_b']:,}")
    print(f"  Total couple matches: {len(couple_matches):,}")
    print(f"  Total conflicts: {len(conflicts):,}")
    
    return couple_matches, conflicts


def generate_couples_csv(
    couple_matches: List[CoupleMatch],
    conflicts: List[CoupleConflict],
    output_dir: str = "."
) -> Tuple[str, str]:
    """Generate CSV files for married couples analysis."""
    print("Generating married couples CSV files...")
    
    # Main CSV headers
    headers = [
        'relationship_id',
        'match_status',
        # Contact A (CiVi)
        'contact_id_a',
        'civi_first_name_a',
        'civi_last_name_a',
        'civi_email_a',
        # VH match for A
        'vh_user_id_a',
        'vh_email_matched_a',
        'vh_match_type_a',
        'vh_first_name_a',
        'vh_last_name_a',
        'vh_primary_email_a',
        # Contact B (CiVi)
        'contact_id_b',
        'civi_first_name_b',
        'civi_last_name_b',
        'civi_email_b',
        # VH match for B
        'vh_user_id_b',
        'vh_email_matched_b',
        'vh_match_type_b',
        'vh_first_name_b',
        'vh_last_name_b',
        'vh_primary_email_b',
    ]
    
    def match_to_row(m: CoupleMatch) -> List[str]:
        return [
            str(m.relationship_id),
            m.match_status.value,
            # A
            str(m.contact_id_a),
            m.civi_first_name_a or '',
            m.civi_last_name_a or '',
            m.civi_email_a or '',
            m.vh_user_id_a or '',
            m.vh_email_matched_a or '',
            m.vh_match_type_a.value if m.vh_match_type_a else '',
            m.vh_first_name_a or '',
            m.vh_last_name_a or '',
            m.vh_primary_email_a or '',
            # B
            str(m.contact_id_b),
            m.civi_first_name_b or '',
            m.civi_last_name_b or '',
            m.civi_email_b or '',
            m.vh_user_id_b or '',
            m.vh_email_matched_b or '',
            m.vh_match_type_b.value if m.vh_match_type_b else '',
            m.vh_first_name_b or '',
            m.vh_last_name_b or '',
            m.vh_primary_email_b or '',
        ]
    
    # Write main CSV
    main_csv_path = f"{output_dir}/married_couples_mapping.csv"
    with open(main_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for match in couple_matches:
            writer.writerow(match_to_row(match))
    print(f"  Written {len(couple_matches):,} records to {main_csv_path}")
    
    # Conflicts CSV headers
    conflict_headers = [
        'relationship_id',
        'contact_id',
        'is_contact_a',
        'civi_first_name',
        'civi_last_name',
        'civi_email',
        'vh_user_id',
        'vh_email_matched',
        'vh_match_type',
        'vh_first_name',
        'vh_last_name',
        'vh_primary_email',
    ]
    
    # Write conflicts CSV (one row per VH match in conflict)
    conflicts_csv_path = f"{output_dir}/married_couples_conflicts.csv"
    conflict_rows = 0
    with open(conflicts_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(conflict_headers)
        for conflict in conflicts:
            for vh_match in conflict.vh_matches:
                writer.writerow([
                    str(conflict.relationship_id),
                    str(conflict.contact_id),
                    'true' if conflict.is_contact_a else 'false',
                    conflict.civi_first_name or '',
                    conflict.civi_last_name or '',
                    conflict.civi_email or '',
                    vh_match[0],  # user_id
                    vh_match[1],  # email_matched
                    vh_match[2].value,  # match_type
                    vh_match[3] or '',  # first_name
                    vh_match[4] or '',  # last_name
                    vh_match[5] or '',  # primary_email
                ])
                conflict_rows += 1
    print(f"  Written {conflict_rows:,} conflict rows to {conflicts_csv_path}")
    
    # Print status summary
    status_counts = Counter(m.match_status for m in couple_matches)
    print("\n  Match status summary:")
    for status in CoupleMatchStatus:
        count = status_counts.get(status, 0)
        pct = (count / len(couple_matches) * 100) if couple_matches else 0
        print(f"    - {status.value}: {count:,} ({pct:.2f}%)")
    
    return main_csv_path, conflicts_csv_path


def generate_report(couple_matches: List[CoupleMatch], conflicts: List[CoupleConflict]) -> None:
    """Generate analysis report for married couples."""
    print("\n" + "=" * 80)
    print("MARRIED COUPLES ANALYSIS REPORT")
    print("=" * 80)
    
    # Overall statistics
    total_couples = len(couple_matches) + len(set(c.relationship_id for c in conflicts))
    
    print(f"\nTotal married couples analyzed: {total_couples:,}")
    
    # Match status breakdown
    print("\n" + "-" * 80)
    print("VH MATCHING STATUS")
    print("-" * 80)
    
    status_counts = Counter(m.match_status for m in couple_matches)
    
    both_matched = status_counts.get(CoupleMatchStatus.BOTH_MATCHED, 0)
    only_a = status_counts.get(CoupleMatchStatus.ONLY_A_MATCHED, 0)
    only_b = status_counts.get(CoupleMatchStatus.ONLY_B_MATCHED, 0)
    neither = status_counts.get(CoupleMatchStatus.NEITHER_MATCHED, 0)
    
    print(f"\nCouples with both spouses matched to VH: {both_matched:,}")
    print(f"Couples with only spouse A matched: {only_a:,}")
    print(f"Couples with only spouse B matched: {only_b:,}")
    print(f"Couples with neither matched: {neither:,}")
    print(f"Couples with conflicts: {len(set(c.relationship_id for c in conflicts)):,}")
    
    # Match type breakdown for matched couples
    print("\n" + "-" * 80)
    print("MATCH TYPE BREAKDOWN")
    print("-" * 80)
    
    match_types_a = Counter(m.vh_match_type_a for m in couple_matches if m.vh_match_type_a)
    match_types_b = Counter(m.vh_match_type_b for m in couple_matches if m.vh_match_type_b)
    
    print("\nSpouse A match types:")
    for mt in MatchType:
        count_a = match_types_a.get(mt, 0)
        print(f"  - {mt.value}: {count_a:,}")
    
    print("\nSpouse B match types:")
    for mt in MatchType:
        count_b = match_types_b.get(mt, 0)
        print(f"  - {mt.value}: {count_b:,}")
    
    # Conflict analysis
    if conflicts:
        print("\n" + "-" * 80)
        print("CONFLICT ANALYSIS")
        print("-" * 80)
        
        conflict_contacts_a = [c for c in conflicts if c.is_contact_a]
        conflict_contacts_b = [c for c in conflicts if not c.is_contact_a]
        
        print(f"\nTotal conflict records: {len(conflicts):,}")
        print(f"  - Spouse A conflicts: {len(conflict_contacts_a):,}")
        print(f"  - Spouse B conflicts: {len(conflict_contacts_b):,}")
        
        # Show some example conflicts
        if conflicts[:3]:
            print("\nExample conflicts:")
            for c in conflicts[:3]:
                spouse = "A" if c.is_contact_a else "B"
                print(f"  Relationship {c.relationship_id}, Spouse {spouse}: "
                      f"{c.civi_first_name} {c.civi_last_name} ({c.civi_email})")
                for vh in c.vh_matches[:2]:
                    print(f"    → VH User {vh[0]}: {vh[3]} {vh[4]} ({vh[5]})")
    
    # Summary for import
    print("\n" + "-" * 80)
    print("IMPORT SUMMARY")
    print("-" * 80)
    
    importable = both_matched + only_a + only_b
    print(f"\nCouples ready for import (at least one spouse matched): {importable:,}")
    print(f"Couples with both spouses matched: {both_matched:,}")
    print(f"Couples needing conflict resolution: {len(set(c.relationship_id for c in conflicts)):,}")
    print(f"Couples with no VH matches: {neither:,}")
    
    print("\n" + "=" * 80)
    print("Report generated successfully!")
    print("=" * 80)


def main():
    """Main execution function."""
    print("=" * 80)
    print("Married Couples Analysis")
    print("=" * 80)
    print()
    
    # Determine output directory (same as script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Create database connections
        civi_engine, replica_engine = get_database_engines()
        print()
        
        # Extract data
        couples_df = extract_civi_couples(civi_engine)
        print()
        
        civi_emails_df = extract_civi_email_data(civi_engine)
        print()
        
        replica_profiles_df = extract_replica_profile_data(replica_engine)
        print()
        
        # Analyze couples
        couple_matches, conflicts = analyze_married_couples(
            couples_df, civi_emails_df, replica_profiles_df
        )
        print()
        
        # Generate CSV files
        main_csv, conflicts_csv = generate_couples_csv(
            couple_matches, conflicts, script_dir
        )
        print()
        
        # Generate report
        generate_report(couple_matches, conflicts)
        
        print("\n" + "=" * 80)
        print("Analysis completed successfully!")
        print("=" * 80)
        print(f"\nCSV files generated:")
        print(f"  - {main_csv}")
        print(f"  - {conflicts_csv}")
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

