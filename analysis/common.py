#!/usr/bin/env python3
"""
Common utilities for CiVi-VH data analysis.
Provides shared database connections, data extraction, and email matching functionality.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import csv


# Database connection strings
CIVI_STAGING_CONN = "mysql+pymysql://staging1pay_testbb_top:***REMOVED***@mysql7:3306/staging1pay_testbb_top"
REPLICA_PROFILES_CONN = "postgresql+psycopg2://user:password@localhost:5432/profiles_replica?sslmode=disable"


class MatchType(Enum):
    """Email match type classification for VH-CiVi user matching."""
    PRIMARY_TO_PRIMARY = "primary_to_primary"  # VH primary ↔ CiVi primary
    PRIMARY_TO_ALT = "primary_to_alt"          # VH primary ↔ CiVi alt
    ALT_TO_PRIMARY = "alt_to_primary"          # VH alt ↔ CiVi primary
    ALT_TO_ALT = "alt_to_alt"                  # VH alt ↔ CiVi alt

    @property
    def priority(self) -> int:
        """Lower number = higher priority."""
        priorities = {
            MatchType.PRIMARY_TO_PRIMARY: 1,
            MatchType.PRIMARY_TO_ALT: 2,
            MatchType.ALT_TO_PRIMARY: 2,
            MatchType.ALT_TO_ALT: 3,
        }
        return priorities[self]


def get_database_engines():
    """Create and return database engines for CiVi and Replica."""
    print("Connecting to databases...")
    civi_engine = create_engine(CIVI_STAGING_CONN, pool_pre_ping=True)
    replica_engine = create_engine(REPLICA_PROFILES_CONN, pool_pre_ping=True)
    print("  ✓ Connected to civi_staging")
    print("  ✓ Connected to replica_profiles")
    return civi_engine, replica_engine


def normalize_email(email: str) -> str:
    """Normalize email for case-insensitive matching."""
    if not email:
        return ""
    return str(email).lower().strip()


def normalize_country(country: str) -> str:
    """Normalize country code (uppercase for ISO codes)."""
    if not country:
        return ""
    return str(country).upper().strip()


def extract_civi_email_data(engine) -> pd.DataFrame:
    """Extract email data from civi_staging.
    
    Extracts both primary and alternative emails for each contact.
    Returns DataFrame with: contact_id, email, is_primary, email_type
    """
    print("Extracting CiVi email data...")
    
    query = text("""
        SELECT 
            ce.contact_id,
            ce.email,
            ce.is_primary,
            CASE 
                WHEN ce.is_primary = 1 THEN 'primary'
                ELSE 'alternative'
            END as email_type
        FROM staging1pay_testbb_top_civi.civicrm_email ce
        INNER JOIN staging1pay_testbb_top_civi.civicrm_contact cc ON ce.contact_id = cc.id
        WHERE ce.email IS NOT NULL AND ce.email != ''
          AND cc.is_deleted = 0
        ORDER BY ce.contact_id, ce.is_primary DESC, ce.id
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        print(f"  Extracted {len(df)} email records")
        print(f"  - Primary emails: {len(df[df['is_primary'] == 1])}")
        print(f"  - Alternative emails: {len(df[df['is_primary'] == 0])}")
        return df
    except Exception as e:
        print(f"  Error extracting email data: {e}")
        return pd.DataFrame()


def extract_civi_contact_data(engine) -> pd.DataFrame:
    """Extract contact names and primary email from CiVi.
    
    Returns DataFrame with: contact_id, first_name, last_name, primary_email
    """
    print("Extracting CiVi contact names and primary emails...")
    
    query = text("""
        SELECT 
            cc.id as contact_id,
            cc.first_name,
            cc.last_name,
            (SELECT ce.email 
             FROM staging1pay_testbb_top_civi.civicrm_email ce 
             WHERE ce.contact_id = cc.id AND ce.is_primary = 1 
             LIMIT 1) as primary_email
        FROM staging1pay_testbb_top_civi.civicrm_contact cc
        WHERE cc.is_deleted = 0
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        print(f"  Extracted {len(df)} contact records")
        return df
    except Exception as e:
        print(f"  Error extracting contact data: {e}")
        return pd.DataFrame()


def extract_replica_profile_data(engine) -> pd.DataFrame:
    """Extract profile data from replica_profiles.
    
    Returns DataFrame with: user_id, primary_email, alternate_email_1, alternate_email_2,
                           country, first_name_latin, last_name_latin
    """
    print("Extracting VH profile data from replica_profiles...")
    
    query = text("""
        SELECT 
            user_id::text as user_id,
            primary_email,
            alternate_email_1,
            alternate_email_2,
            country,
            first_name_latin,
            last_name_latin
        FROM users
        WHERE deleted = false
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        print(f"  Extracted {len(df)} profile records")
        print(f"  - Users with primary_email: {df['primary_email'].notna().sum()}")
        print(f"  - Users with alternate_email_1: {df['alternate_email_1'].notna().sum()}")
        print(f"  - Users with alternate_email_2: {df['alternate_email_2'].notna().sum()}")
        print(f"  - Users with country: {df['country'].notna().sum()}")
        return df
    except Exception as e:
        print(f"  Error extracting replica profile data: {e}")
        return pd.DataFrame()


def build_civi_email_lookup(civi_emails_df: pd.DataFrame) -> Dict[str, List[Tuple[int, bool]]]:
    """Build CiVi email lookup: normalized_email -> list of (contact_id, is_primary)"""
    civi_email_lookup: Dict[str, List[Tuple[int, bool]]] = {}
    for _, row in civi_emails_df.iterrows():
        email_norm = normalize_email(row['email'])
        if not email_norm:
            continue
        contact_id = row['contact_id']
        is_primary = row['is_primary'] == 1
        if email_norm not in civi_email_lookup:
            civi_email_lookup[email_norm] = []
        civi_email_lookup[email_norm].append((contact_id, is_primary))
    return civi_email_lookup


def build_civi_contact_lookup(civi_contacts_df: pd.DataFrame) -> Dict[int, Tuple[str, str, str]]:
    """Build CiVi contact info lookup: contact_id -> (first_name, last_name, primary_email)"""
    civi_contact_lookup: Dict[int, Tuple[str, str, str]] = {}
    for _, row in civi_contacts_df.iterrows():
        civi_contact_lookup[row['contact_id']] = (
            row['first_name'] if pd.notna(row['first_name']) else None,
            row['last_name'] if pd.notna(row['last_name']) else None,
            row['primary_email'] if pd.notna(row['primary_email']) else None
        )
    return civi_contact_lookup


def find_civi_matches_for_vh_user(
    vh_row: pd.Series,
    civi_email_lookup: Dict[str, List[Tuple[int, bool]]]
) -> Dict[int, Tuple[str, MatchType]]:
    """Find all CiVi contacts matching a VH user's emails.
    
    Returns: contact_id -> (email_matched, match_type)
    """
    # Collect VH emails with their type
    vh_emails = []
    if pd.notna(vh_row['primary_email']):
        vh_emails.append((normalize_email(vh_row['primary_email']), True))
    if pd.notna(vh_row['alternate_email_1']):
        vh_emails.append((normalize_email(vh_row['alternate_email_1']), False))
    if pd.notna(vh_row['alternate_email_2']):
        vh_emails.append((normalize_email(vh_row['alternate_email_2']), False))
    
    # Find all CiVi contacts matching any of VH user's emails
    # contact_id -> best match info (email_matched, match_type)
    contact_matches: Dict[int, Tuple[str, MatchType]] = {}
    
    for vh_email, vh_is_primary in vh_emails:
        if not vh_email or vh_email not in civi_email_lookup:
            continue
        
        for civi_contact_id, civi_is_primary in civi_email_lookup[vh_email]:
            # Determine match type
            if vh_is_primary and civi_is_primary:
                match_type = MatchType.PRIMARY_TO_PRIMARY
            elif vh_is_primary and not civi_is_primary:
                match_type = MatchType.PRIMARY_TO_ALT
            elif not vh_is_primary and civi_is_primary:
                match_type = MatchType.ALT_TO_PRIMARY
            else:
                match_type = MatchType.ALT_TO_ALT
            
            # Keep the best match type for this contact
            if civi_contact_id not in contact_matches:
                contact_matches[civi_contact_id] = (vh_email, match_type)
            else:
                existing_match_type = contact_matches[civi_contact_id][1]
                if match_type.priority < existing_match_type.priority:
                    contact_matches[civi_contact_id] = (vh_email, match_type)
    
    return contact_matches


def find_vh_match_for_civi_contact(
    contact_id: int,
    civi_emails_df: pd.DataFrame,
    replica_profiles_df: pd.DataFrame
) -> Optional[Tuple[str, str, MatchType]]:
    """Find VH user matching a CiVi contact by email.
    
    Returns: (user_id, email_matched, match_type) or None if no match
    """
    # Build email lookup for VH users: email -> (user_id, is_primary)
    vh_email_lookup: Dict[str, Tuple[str, bool]] = {}
    for _, row in replica_profiles_df.iterrows():
        user_id = row['user_id']
        if pd.notna(row['primary_email']):
            email_norm = normalize_email(row['primary_email'])
            if email_norm and email_norm not in vh_email_lookup:
                vh_email_lookup[email_norm] = (user_id, True)
        if pd.notna(row['alternate_email_1']):
            email_norm = normalize_email(row['alternate_email_1'])
            if email_norm and email_norm not in vh_email_lookup:
                vh_email_lookup[email_norm] = (user_id, False)
        if pd.notna(row['alternate_email_2']):
            email_norm = normalize_email(row['alternate_email_2'])
            if email_norm and email_norm not in vh_email_lookup:
                vh_email_lookup[email_norm] = (user_id, False)
    
    # Get all emails for this CiVi contact
    contact_emails = civi_emails_df[civi_emails_df['contact_id'] == contact_id]
    
    best_match = None
    best_priority = 999
    
    for _, email_row in contact_emails.iterrows():
        email_norm = normalize_email(email_row['email'])
        if not email_norm or email_norm not in vh_email_lookup:
            continue
        
        civi_is_primary = email_row['is_primary'] == 1
        vh_user_id, vh_is_primary = vh_email_lookup[email_norm]
        
        # Determine match type
        if civi_is_primary and vh_is_primary:
            match_type = MatchType.PRIMARY_TO_PRIMARY
        elif civi_is_primary and not vh_is_primary:
            match_type = MatchType.PRIMARY_TO_ALT  
        elif not civi_is_primary and vh_is_primary:
            match_type = MatchType.ALT_TO_PRIMARY
        else:
            match_type = MatchType.ALT_TO_ALT
        
        if match_type.priority < best_priority:
            best_priority = match_type.priority
            best_match = (vh_user_id, email_norm, match_type)
    
    return best_match

