#!/usr/bin/env python3
"""
Country and email matching analysis between civi_staging and replica_profiles.
This script connects directly to both databases and performs comprehensive analysis.
Generates CSV files for CiVi-to-VH data sync pipeline.

Usage:
    python analyze_country_email.py
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
    normalize_country,
    extract_civi_email_data,
    extract_civi_contact_data,
    extract_replica_profile_data,
    build_civi_email_lookup,
    build_civi_contact_lookup,
    find_civi_matches_for_vh_user,
)


class CountryStatus(Enum):
    """Country comparison status between VH and CiVi."""
    MISSING_IN_BOTH = "missing_in_both"
    MISSING_IN_CIVI = "missing_in_civi"
    MISSING_IN_VH = "missing_in_vh"
    EQUALS = "equals"
    DIFFERENT = "different"


@dataclass
class UserMatch:
    """Represents a match between a VH user and a CiVi contact."""
    user_id: str
    contact_id: int
    email_matched: str
    match_type: MatchType
    vh_primary_email: str
    vh_alt_email_1: Optional[str]
    vh_alt_email_2: Optional[str]
    civi_primary_email: Optional[str]
    vh_first_name: Optional[str]
    vh_last_name: Optional[str]
    civi_first_name: Optional[str]
    civi_last_name: Optional[str]
    vh_country: Optional[str]
    civi_country: Optional[str]
    country_status: CountryStatus


def extract_civi_country_data(engine) -> pd.DataFrame:
    """Extract Country Data from civi_staging
    
    Prefers custom field (civicrm_value_bb_country_256) over built-in schema.
    Falls back to built-in schema (civicrm_address + civicrm_country) when custom field is empty.
    """
    print("Extracting CiVi country data...")
    
    query = text("""
        SELECT 
            cc.id as contact_id,
            COALESCE(cvbc.bb_country_1629, ccy.iso_code) as country,
            CASE 
                WHEN cvbc.bb_country_1629 IS NOT NULL AND cvbc.bb_country_1629 != '' THEN 'custom'
                WHEN ccy.iso_code IS NOT NULL THEN 'builtin'
                ELSE NULL
            END as source
        FROM staging1pay_testbb_top_civi.civicrm_contact cc
        LEFT JOIN staging1pay_testbb_top_civi.civicrm_value_bb_country_256 cvbc 
            ON cc.id = cvbc.entity_id
        LEFT JOIN staging1pay_testbb_top_civi.civicrm_address ca 
            ON cc.id = ca.contact_id AND ca.is_primary = 1
        LEFT JOIN staging1pay_testbb_top_civi.civicrm_country ccy 
            ON ca.country_id = ccy.id
        WHERE COALESCE(cvbc.bb_country_1629, ccy.iso_code) IS NOT NULL
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        print(f"  Extracted {len(df)} country records")
        print(f"  - Custom field records: {len(df[df['source'] == 'custom'])}")
        print(f"  - Built-in schema records: {len(df[df['source'] == 'builtin'])}")
        return df
    except Exception as e:
        print(f"  Error extracting country data: {e}")
        return pd.DataFrame()


def get_country_list(engine) -> Set[str]:
    """Get valid country codes from country_list table in replica_profiles."""
    query = text("""
        SELECT code
        FROM country_list
        WHERE code IS NOT NULL AND code != ''
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return set(df['code'].str.upper().str.strip())
    except Exception as e:
        print(f"  Warning: Could not fetch country_list: {e}")
        return set()


def analyze_email_matching(civi_emails_df: pd.DataFrame, replica_profiles_df: pd.DataFrame) -> Dict:
    """Perform Email Matching Analysis
    
    Analyzes all 6 matching combinations between CiVi and VH emails.
    """
    print("Performing email matching analysis...")
    
    # Build normalized email sets from civi_staging
    civi_primary_emails = set()
    civi_alternative_emails = set()
    
    for _, row in civi_emails_df.iterrows():
        email_norm = normalize_email(row['email'])
        if not email_norm:
            continue
        if row['is_primary'] == 1:
            civi_primary_emails.add(email_norm)
        else:
            civi_alternative_emails.add(email_norm)
    
    # Build normalized email sets from replica_profiles
    replica_primary_emails = set()
    replica_alt1_emails = set()
    replica_alt2_emails = set()
    
    for _, row in replica_profiles_df.iterrows():
        if pd.notna(row['primary_email']):
            email_norm = normalize_email(row['primary_email'])
            if email_norm:
                replica_primary_emails.add(email_norm)
        if pd.notna(row['alternate_email_1']):
            email_norm = normalize_email(row['alternate_email_1'])
            if email_norm:
                replica_alt1_emails.add(email_norm)
        if pd.notna(row['alternate_email_2']):
            email_norm = normalize_email(row['alternate_email_2'])
            if email_norm:
                replica_alt2_emails.add(email_norm)
    
    # Calculate matches
    primary_to_primary = civi_primary_emails.intersection(replica_primary_emails)
    primary_to_alt1 = civi_primary_emails.intersection(replica_alt1_emails)
    primary_to_alt2 = civi_primary_emails.intersection(replica_alt2_emails)
    
    alt_to_primary = civi_alternative_emails.intersection(replica_primary_emails)
    alt_to_alt1 = civi_alternative_emails.intersection(replica_alt1_emails)
    alt_to_alt2 = civi_alternative_emails.intersection(replica_alt2_emails)
    
    # Overall statistics
    all_civi_emails = civi_primary_emails.union(civi_alternative_emails)
    all_replica_emails = replica_primary_emails.union(replica_alt1_emails).union(replica_alt2_emails)
    total_unique_matches = all_civi_emails.intersection(all_replica_emails)
    
    # Unmatched emails
    unmatched_civi_primary = civi_primary_emails - all_replica_emails
    unmatched_civi_alt = civi_alternative_emails - all_replica_emails
    
    stats = {
        'primary_email_matches': {
            'primary_to_primary': len(primary_to_primary),
            'primary_to_alt1': len(primary_to_alt1),
            'primary_to_alt2': len(primary_to_alt2),
            'total_primary_matches': len(primary_to_primary) + len(primary_to_alt1) + len(primary_to_alt2)
        },
        'alternative_email_matches': {
            'alt_to_primary': len(alt_to_primary),
            'alt_to_alt1': len(alt_to_alt1),
            'alt_to_alt2': len(alt_to_alt2),
            'total_alt_matches': len(alt_to_primary) + len(alt_to_alt1) + len(alt_to_alt2)
        },
        'overall_email_matching': {
            'total_unique_civi_emails': len(all_civi_emails),
            'total_unique_replica_emails': len(all_replica_emails),
            'total_unique_matches': len(total_unique_matches),
            'match_rate_percent': (len(total_unique_matches) / len(all_civi_emails) * 100) if len(all_civi_emails) > 0 else 0
        },
        'unmatched_emails': {
            'unmatched_civi_primary_count': len(unmatched_civi_primary),
            'unmatched_civi_alt_count': len(unmatched_civi_alt),
            'total_unmatched_civi': len(unmatched_civi_primary) + len(unmatched_civi_alt)
        }
    }
    
    print("  Email matching analysis completed")
    return stats


def analyze_country_matching(civi_country_df: pd.DataFrame, replica_profiles_df: pd.DataFrame, 
                            valid_country_codes: Set[str]) -> Dict:
    """Perform Country Matching Analysis
    
    Analyzes country distribution, matching, and validation.
    """
    print("Performing country matching analysis...")
    
    # Build country distribution from civi_staging
    civi_country_dist = Counter()
    civi_countries_by_source = {'custom': Counter(), 'builtin': Counter()}
    
    for _, row in civi_country_df.iterrows():
        country = normalize_country(row['country'])
        if country:
            civi_country_dist[country] += 1
            source = row.get('source', 'unknown')
            if source in civi_countries_by_source:
                civi_countries_by_source[source][country] += 1
    
    # Build country distribution from replica_profiles
    replica_country_dist = Counter()
    for _, row in replica_profiles_df.iterrows():
        if pd.notna(row['country']):
            country = normalize_country(row['country'])
            if country:
                replica_country_dist[country] += 1
    
    # Country sets
    civi_countries_set = set(civi_country_dist.keys())
    replica_countries_set = set(replica_country_dist.keys())
    
    # Matching analysis
    matched_countries = civi_countries_set.intersection(replica_countries_set)
    unmatched_in_civi = civi_countries_set - replica_countries_set
    unmatched_in_replica = replica_countries_set - civi_countries_set
    
    # Validation against country_list
    valid_countries = civi_countries_set.intersection(valid_country_codes)
    invalid_countries = civi_countries_set - valid_country_codes
    
    # Build detailed country match stats (all countries)
    country_match_stats = {}
    for country, count in civi_country_dist.items():
        country_match_stats[country] = {
            'civi_count': count,
            'replica_count': replica_country_dist.get(country, 0),
            'matched': country in matched_countries,
            'valid': country in valid_country_codes,
            'custom_field_count': civi_countries_by_source['custom'].get(country, 0),
            'builtin_count': civi_countries_by_source['builtin'].get(country, 0)
        }
    
    # Current vs potential coverage
    current_coverage = replica_profiles_df['country'].notna().sum()
    total_users = len(replica_profiles_df)
    users_without_country = total_users - current_coverage
    
    stats = {
        'total_unique_countries_civi': len(civi_countries_set),
        'total_unique_countries_replica': len(replica_countries_set),
        'matched_countries_count': len(matched_countries),
        'unmatched_in_civi_count': len(unmatched_in_civi),
        'unmatched_in_replica_count': len(unmatched_in_replica),
        'valid_countries_count': len(valid_countries),
        'invalid_countries_count': len(invalid_countries),
        'country_distribution_civi': dict(civi_country_dist),
        'country_distribution_replica': dict(replica_country_dist),
        'country_match_stats': country_match_stats,
        'matched_countries_list': sorted(list(matched_countries)),
        'unmatched_in_civi_list': sorted(list(unmatched_in_civi)),
        'unmatched_in_replica_list': sorted(list(unmatched_in_replica)),
        'invalid_countries_list': sorted(list(invalid_countries)),
        'coverage_analysis': {
            'current_users_with_country': current_coverage,
            'current_users_without_country': users_without_country,
            'total_users': total_users
        }
    }
    
    print("  Country matching analysis completed")
    return stats


def analyze_user_country_comparison(civi_emails_df: pd.DataFrame, civi_country_df: pd.DataFrame,
                                   replica_profiles_df: pd.DataFrame) -> Dict:
    """Perform User-Country Comparison Analysis
    
    Matches users by email and compares country values between matched pairs.
    """
    print("Performing user-country comparison analysis...")
    
    # Build email mappings from civi_staging
    civi_email_to_contact = {}
    civi_primary_emails = set()
    civi_alt_emails = set()
    
    for _, row in civi_emails_df.iterrows():
        email_norm = normalize_email(row['email'])
        if not email_norm:
            continue
        contact_id = row['contact_id']
        if row['is_primary'] == 1:
            if email_norm not in civi_email_to_contact:
                civi_email_to_contact[email_norm] = contact_id
            civi_primary_emails.add(email_norm)
        else:
            if email_norm not in civi_email_to_contact:
                civi_email_to_contact[email_norm] = contact_id
            civi_alt_emails.add(email_norm)
    
    # Build email mappings from replica_profiles
    replica_email_to_user = {}
    replica_primary_emails = set()
    replica_alt_emails = set()
    
    for _, row in replica_profiles_df.iterrows():
        user_id = row['user_id']
        if pd.notna(row['primary_email']):
            email_norm = normalize_email(row['primary_email'])
            if email_norm:
                if email_norm not in replica_email_to_user:
                    replica_email_to_user[email_norm] = user_id
                replica_primary_emails.add(email_norm)
        if pd.notna(row['alternate_email_1']):
            email_norm = normalize_email(row['alternate_email_1'])
            if email_norm:
                if email_norm not in replica_email_to_user:
                    replica_email_to_user[email_norm] = user_id
                replica_alt_emails.add(email_norm)
        if pd.notna(row['alternate_email_2']):
            email_norm = normalize_email(row['alternate_email_2'])
            if email_norm:
                if email_norm not in replica_email_to_user:
                    replica_email_to_user[email_norm] = user_id
                replica_alt_emails.add(email_norm)
    
    # Match users by email (preferring primary-to-primary)
    contact_to_user = {}
    matched_emails = set()
    
    # Priority 1: Primary to Primary
    for email in civi_primary_emails.intersection(replica_primary_emails):
        if email not in matched_emails:
            contact_id = civi_email_to_contact[email]
            user_id = replica_email_to_user[email]
            if contact_id not in contact_to_user:
                contact_to_user[contact_id] = user_id
                matched_emails.add(email)
    
    # Priority 2: Primary to Alternate
    for email in civi_primary_emails.intersection(replica_alt_emails):
        if email not in matched_emails:
            contact_id = civi_email_to_contact[email]
            user_id = replica_email_to_user[email]
            if contact_id not in contact_to_user:
                contact_to_user[contact_id] = user_id
                matched_emails.add(email)
    
    # Priority 3: Alternate to Primary
    for email in civi_alt_emails.intersection(replica_primary_emails):
        if email not in matched_emails:
            contact_id = civi_email_to_contact[email]
            user_id = replica_email_to_user[email]
            if contact_id not in contact_to_user:
                contact_to_user[contact_id] = user_id
                matched_emails.add(email)
    
    # Priority 4: Alternate to Alternate
    for email in civi_alt_emails.intersection(replica_alt_emails):
        if email not in matched_emails:
            contact_id = civi_email_to_contact[email]
            user_id = replica_email_to_user[email]
            if contact_id not in contact_to_user:
                contact_to_user[contact_id] = user_id
                matched_emails.add(email)
    
    # Build country lookup dictionaries
    civi_country_by_contact = {}
    for _, row in civi_country_df.iterrows():
        contact_id = row['contact_id']
        country = normalize_country(row['country'])
        if country:
            civi_country_by_contact[contact_id] = country
    
    replica_country_by_user = {}
    for _, row in replica_profiles_df.iterrows():
        user_id = row['user_id']
        if pd.notna(row['country']):
            country = normalize_country(row['country'])
            if country:
                replica_country_by_user[user_id] = country
    
    # Compare countries for matched pairs
    missing_in_both = 0
    missing_only_in_civi = 0
    missing_only_in_vh = 0
    exists_and_equals = 0
    exists_but_different = 0
    
    for contact_id, user_id in contact_to_user.items():
        civi_country = civi_country_by_contact.get(contact_id, "")
        replica_country = replica_country_by_user.get(user_id, "")
        
        civi_has_country = bool(civi_country)
        replica_has_country = bool(replica_country)
        
        if not civi_has_country and not replica_has_country:
            missing_in_both += 1
        elif not civi_has_country and replica_has_country:
            missing_only_in_civi += 1
        elif civi_has_country and not replica_has_country:
            missing_only_in_vh += 1
        elif civi_country == replica_country:
            exists_and_equals += 1
        else:
            exists_but_different += 1
    
    total_matched = len(contact_to_user)
    
    stats = {
        'total_matched_users': total_matched,
        'missing_in_both': missing_in_both,
        'missing_only_in_civi': missing_only_in_civi,
        'missing_only_in_vh': missing_only_in_vh,
        'exists_and_equals': exists_and_equals,
        'exists_but_different': exists_but_different
    }
    
    print(f"  Matched {total_matched:,} user pairs by email")
    print(f"  - Missing in both: {missing_in_both:,}")
    print(f"  - Missing only in civi: {missing_only_in_civi:,}")
    print(f"  - Missing only in vh: {missing_only_in_vh:,}")
    print(f"  - Exists and equals: {exists_and_equals:,}")
    print(f"  - Exists but different: {exists_but_different:,}")
    
    return stats


def build_vh_centric_user_mapping(
    civi_emails_df: pd.DataFrame,
    civi_country_df: pd.DataFrame,
    civi_contacts_df: pd.DataFrame,
    replica_profiles_df: pd.DataFrame
) -> Tuple[List[UserMatch], List[UserMatch]]:
    """Build VH-centric user mapping between VH users and CiVi contacts.
    
    Auto-merge is based on country matching: if all matched CiVi contacts have
    the same (or null) country, pick the best match. Otherwise, it's a conflict.
    
    Returns:
        Tuple of (unique_matches, conflict_matches)
    """
    print("Building VH-centric user mapping...")
    
    # Build lookups
    civi_email_lookup = build_civi_email_lookup(civi_emails_df)
    civi_contact_lookup = build_civi_contact_lookup(civi_contacts_df)
    
    # Build CiVi country lookup: contact_id -> country
    civi_country_lookup: Dict[int, str] = {}
    for _, row in civi_country_df.iterrows():
        country = normalize_country(row['country'])
        if country:
            civi_country_lookup[row['contact_id']] = country
    
    unique_matches: List[UserMatch] = []
    conflict_matches: List[UserMatch] = []
    
    stats = {
        'total_vh_users': 0,
        'vh_users_with_match': 0,
        'vh_users_no_match': 0,
        'vh_users_unique_match': 0,
        'vh_users_auto_merged': 0,
        'vh_users_conflict': 0,
    }
    
    # Iterate over VH users
    for _, vh_row in replica_profiles_df.iterrows():
        stats['total_vh_users'] += 1
        user_id = vh_row['user_id']
        
        # Find CiVi contacts matching this VH user
        contact_matches = find_civi_matches_for_vh_user(vh_row, civi_email_lookup)
        
        if not contact_matches:
            stats['vh_users_no_match'] += 1
            continue
        
        stats['vh_users_with_match'] += 1
        
        # Prepare common VH data
        vh_country = normalize_country(vh_row['country']) if pd.notna(vh_row['country']) else None
        
        # Create UserMatch objects for all matches
        matches_for_user: List[UserMatch] = []
        for contact_id, (email_matched, match_type) in contact_matches.items():
            civi_country = civi_country_lookup.get(contact_id)
            civi_info = civi_contact_lookup.get(contact_id, (None, None, None))
            
            # Determine country status
            if not vh_country and not civi_country:
                country_status = CountryStatus.MISSING_IN_BOTH
            elif not civi_country:
                country_status = CountryStatus.MISSING_IN_CIVI
            elif not vh_country:
                country_status = CountryStatus.MISSING_IN_VH
            elif vh_country == civi_country:
                country_status = CountryStatus.EQUALS
            else:
                country_status = CountryStatus.DIFFERENT
            
            match = UserMatch(
                user_id=user_id,
                contact_id=contact_id,
                email_matched=email_matched,
                match_type=match_type,
                vh_primary_email=vh_row['primary_email'] if pd.notna(vh_row['primary_email']) else None,
                vh_alt_email_1=vh_row['alternate_email_1'] if pd.notna(vh_row['alternate_email_1']) else None,
                vh_alt_email_2=vh_row['alternate_email_2'] if pd.notna(vh_row['alternate_email_2']) else None,
                civi_primary_email=civi_info[2],
                vh_first_name=vh_row['first_name_latin'] if pd.notna(vh_row['first_name_latin']) else None,
                vh_last_name=vh_row['last_name_latin'] if pd.notna(vh_row['last_name_latin']) else None,
                civi_first_name=civi_info[0],
                civi_last_name=civi_info[1],
                vh_country=vh_country,
                civi_country=civi_country,
                country_status=country_status
            )
            matches_for_user.append(match)
        
        # Separate unique vs conflict
        if len(matches_for_user) == 1:
            stats['vh_users_unique_match'] += 1
            unique_matches.append(matches_for_user[0])
        else:
            # Multiple CiVi contacts - check if we can auto-merge
            # Auto-merge if all contacts with a country have the SAME country
            non_null_countries = set(m.civi_country for m in matches_for_user if m.civi_country)
            
            if len(non_null_countries) <= 1:
                # All same country (or all null) - auto-merge by picking best match
                stats['vh_users_auto_merged'] += 1
                best_match = min(
                    matches_for_user,
                    key=lambda m: (
                        0 if m.civi_country else 1,  # Prefer non-null country
                        m.match_type.priority,
                        m.contact_id
                    )
                )
                unique_matches.append(best_match)
            else:
                # Different non-null countries - true conflict
                stats['vh_users_conflict'] += 1
                conflict_matches.extend(matches_for_user)
    
    print(f"  Total VH users: {stats['total_vh_users']:,}")
    print(f"  - With match: {stats['vh_users_with_match']:,}")
    print(f"  - No match: {stats['vh_users_no_match']:,}")
    print(f"  - Unique match (single contact): {stats['vh_users_unique_match']:,}")
    print(f"  - Auto-merged (same country): {stats['vh_users_auto_merged']:,}")
    print(f"  - True conflicts (diff country): {stats['vh_users_conflict']:,}")
    print(f"  Total unique match records: {len(unique_matches):,}")
    print(f"  Conflict match records: {len(conflict_matches):,}")
    
    return unique_matches, conflict_matches


def generate_sync_csv(
    unique_matches: List[UserMatch],
    conflict_matches: List[UserMatch],
    output_dir: str = "."
) -> Tuple[str, str]:
    """Generate CSV files for CiVi-to-VH data sync."""
    print("Generating sync CSV files...")
    
    headers = [
        'user_id',
        'vh_primary_email',
        'vh_alt_email_1',
        'vh_alt_email_2',
        'contact_id',
        'civi_primary_email',
        'email_matched',
        'match_type',
        'vh_first_name',
        'vh_last_name',
        'civi_first_name',
        'civi_last_name',
        'vh_country',
        'civi_country',
        'country_status',
    ]
    
    def match_to_row(match: UserMatch) -> List[str]:
        return [
            match.user_id,
            match.vh_primary_email or '',
            match.vh_alt_email_1 or '',
            match.vh_alt_email_2 or '',
            str(match.contact_id),
            match.civi_primary_email or '',
            match.email_matched,
            match.match_type.value,
            match.vh_first_name or '',
            match.vh_last_name or '',
            match.civi_first_name or '',
            match.civi_last_name or '',
            match.vh_country or '',
            match.civi_country or '',
            match.country_status.value,
        ]
    
    # Write main CSV
    main_csv_path = f"{output_dir}/user_mapping.csv"
    with open(main_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for match in unique_matches:
            writer.writerow(match_to_row(match))
    print(f"  Written {len(unique_matches):,} records to {main_csv_path}")
    
    # Write conflicts CSV
    conflicts_csv_path = f"{output_dir}/user_mapping_conflicts.csv"
    with open(conflicts_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for match in conflict_matches:
            writer.writerow(match_to_row(match))
    print(f"  Written {len(conflict_matches):,} records to {conflicts_csv_path}")
    
    # Print country status summary for unique matches
    status_counts = Counter(m.country_status for m in unique_matches)
    print("\n  Country status summary (unique matches):")
    for status in CountryStatus:
        count = status_counts.get(status, 0)
        pct = (count / len(unique_matches) * 100) if unique_matches else 0
        print(f"    - {status.value}: {count:,} ({pct:.2f}%)")
    
    # Print match type summary
    match_type_counts = Counter(m.match_type for m in unique_matches)
    print("\n  Match type summary (unique matches):")
    for mt in MatchType:
        count = match_type_counts.get(mt, 0)
        pct = (count / len(unique_matches) * 100) if unique_matches else 0
        print(f"    - {mt.value}: {count:,} ({pct:.2f}%)")
    
    return main_csv_path, conflicts_csv_path


def generate_report(email_stats: Dict, country_stats: Dict, user_country_comparison_stats: Dict) -> None:
    """Generate Final Report"""
    print("\n" + "=" * 80)
    print("COUNTRY AND EMAIL MATCHING ANALYSIS REPORT")
    print("=" * 80)
    
    # Email Matching Statistics
    print("\n" + "-" * 80)
    print("EMAIL MATCHING STATISTICS")
    print("-" * 80)
    
    print("\nPrimary Email Matching:")
    p_matches = email_stats['primary_email_matches']
    print(f"  - CiviCRM Primary → Replica Primary Email: {p_matches['primary_to_primary']:,}")
    print(f"  - CiviCRM Primary → Replica Alternate Email 1: {p_matches['primary_to_alt1']:,}")
    print(f"  - CiviCRM Primary → Replica Alternate Email 2: {p_matches['primary_to_alt2']:,}")
    print(f"  - Total Primary Email Matches: {p_matches['total_primary_matches']:,}")
    
    print("\nAlternative Email Matching:")
    a_matches = email_stats['alternative_email_matches']
    print(f"  - CiviCRM Alternative → Replica Primary Email: {a_matches['alt_to_primary']:,}")
    print(f"  - CiviCRM Alternative → Replica Alternate Email 1: {a_matches['alt_to_alt1']:,}")
    print(f"  - CiviCRM Alternative → Replica Alternate Email 2: {a_matches['alt_to_alt2']:,}")
    print(f"  - Total Alternative Email Matches: {a_matches['total_alt_matches']:,}")
    
    print("\nOverall Email Matching:")
    overall = email_stats['overall_email_matching']
    print(f"  - Total Unique CiviCRM Emails: {overall['total_unique_civi_emails']:,}")
    print(f"  - Total Unique Replica Emails: {overall['total_unique_replica_emails']:,}")
    print(f"  - Total Unique Matches: {overall['total_unique_matches']:,}")
    print(f"  - Match Rate: {overall['match_rate_percent']:.2f}%")
    
    unmatched = email_stats['unmatched_emails']
    print("\nUnmatched Emails:")
    print(f"  - Unmatched CiviCRM Primary Emails: {unmatched['unmatched_civi_primary_count']:,}")
    print(f"  - Unmatched CiviCRM Alternative Emails: {unmatched['unmatched_civi_alt_count']:,}")
    print(f"  - Total Unmatched CiviCRM Emails: {unmatched['total_unmatched_civi']:,}")
    
    # Country Matching Statistics
    print("\n" + "-" * 80)
    print("COUNTRY MATCHING STATISTICS")
    print("-" * 80)
    
    print(f"\nTotal Unique Countries in CiviCRM: {country_stats['total_unique_countries_civi']}")
    print(f"Total Unique Countries in Replica: {country_stats['total_unique_countries_replica']}")
    print(f"Matched Countries: {country_stats['matched_countries_count']}")
    print(f"Unmatched in CiviCRM (not in Replica): {country_stats['unmatched_in_civi_count']}")
    print(f"Unmatched in Replica (not in CiviCRM): {country_stats['unmatched_in_replica_count']}")
    print(f"Valid Countries (in country_list): {country_stats['valid_countries_count']}")
    print(f"Invalid Countries (not in country_list): {country_stats['invalid_countries_count']}")
    
    # Coverage Analysis
    coverage = country_stats['coverage_analysis']
    print("\nCountry Coverage in Replica:")
    print(f"  - Current Users with Country: {coverage['current_users_with_country']:,}")
    print(f"  - Current Users without Country: {coverage['current_users_without_country']:,}")
    print(f"  - Total Users: {coverage['total_users']:,}")
    
    # Full Country Distribution
    print("\n" + "-" * 80)
    print("FULL COUNTRY DISTRIBUTION IN CIVICRM")
    print("-" * 80)
    
    matched_list = set(country_stats['matched_countries_list'])
    invalid_list = set(country_stats['invalid_countries_list'])
    
    country_dist = country_stats['country_distribution_civi']
    for country, count in sorted(country_dist.items(), key=lambda x: x[1], reverse=True):
        match_marker = "✓" if country in matched_list else "✗"
        valid_marker = "✓" if country not in invalid_list else "⚠"
        stats = country_stats['country_match_stats'][country]
        source_info = f" (custom:{stats['custom_field_count']}, builtin:{stats['builtin_count']})"
        print(f"  {match_marker} {valid_marker} {country}: {count:,} contacts{source_info}")
    
    # Invalid Countries
    if country_stats['invalid_countries_list']:
        print("\n" + "-" * 80)
        print("INVALID COUNTRIES (not in country_list)")
        print("-" * 80)
        for country in country_stats['invalid_countries_list']:
            count = country_dist.get(country, 0)
            print(f"  ⚠ {country}: {count:,} contacts")
    
    # User-Country Comparison Statistics
    print("\n" + "-" * 80)
    print("USER-COUNTRY COMPARISON")
    print("-" * 80)
    
    total_matched = user_country_comparison_stats['total_matched_users']
    if total_matched > 0:
        print(f"\nTotal Matched User Pairs: {total_matched:,}")
        print("\nCountry Comparison Results:")
        print(f"  - Missing in both: {user_country_comparison_stats['missing_in_both']:,} ({user_country_comparison_stats['missing_in_both']/total_matched*100:.2f}%)")
        print(f"  - Missing only in civi: {user_country_comparison_stats['missing_only_in_civi']:,} ({user_country_comparison_stats['missing_only_in_civi']/total_matched*100:.2f}%)")
        print(f"  - Missing only in vh: {user_country_comparison_stats['missing_only_in_vh']:,} ({user_country_comparison_stats['missing_only_in_vh']/total_matched*100:.2f}%)")
        print(f"  - Exists and equals: {user_country_comparison_stats['exists_and_equals']:,} ({user_country_comparison_stats['exists_and_equals']/total_matched*100:.2f}%)")
        print(f"  - Exists but different: {user_country_comparison_stats['exists_but_different']:,} ({user_country_comparison_stats['exists_but_different']/total_matched*100:.2f}%)")
    else:
        print("\nNo matched user pairs found.")
    
    print("\n" + "=" * 80)
    print("Report generated successfully!")
    print("=" * 80)


def main():
    """Main execution function."""
    print("=" * 80)
    print("Country and Email Matching Analysis")
    print("=" * 80)
    print()
    
    # Determine output directory (same as script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Create database connections
        civi_engine, replica_engine = get_database_engines()
        print()
        
        # Extract data
        civi_country_df = extract_civi_country_data(civi_engine)
        print()
        
        civi_email_df = extract_civi_email_data(civi_engine)
        print()
        
        civi_contacts_df = extract_civi_contact_data(civi_engine)
        print()
        
        replica_profiles_df = extract_replica_profile_data(replica_engine)
        print()
        
        # Get valid country codes
        print("Fetching valid country codes from country_list...")
        valid_country_codes = get_country_list(replica_engine)
        print(f"  Found {len(valid_country_codes)} valid country codes")
        print()
        
        # Perform analysis
        email_stats = analyze_email_matching(civi_email_df, replica_profiles_df)
        print()
        
        country_stats = analyze_country_matching(civi_country_df, replica_profiles_df, valid_country_codes)
        print()
        
        user_country_comparison_stats = analyze_user_country_comparison(
            civi_email_df, civi_country_df, replica_profiles_df
        )
        print()
        
        # Build VH-centric user mapping and generate CSV files
        unique_matches, conflict_matches = build_vh_centric_user_mapping(
            civi_email_df, civi_country_df, civi_contacts_df, replica_profiles_df
        )
        print()
        
        main_csv, conflicts_csv = generate_sync_csv(unique_matches, conflict_matches, script_dir)
        print()
        
        # Generate report
        generate_report(email_stats, country_stats, user_country_comparison_stats)
        
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
