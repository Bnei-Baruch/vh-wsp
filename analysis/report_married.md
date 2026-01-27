================================================================================
Married Couples Analysis
================================================================================

Connecting to databases...
  ✓ Connected to civi_staging
  ✓ Connected to replica_profiles

Extracting married couples from CiVi...
  Extracted 424 active married couples

Extracting CiVi email data...
  Extracted 60009 email records
  - Primary emails: 59458
  - Alternative emails: 551

Extracting VH profile data from replica_profiles...
  Extracted 16593 profile records
  - Users with primary_email: 16593
  - Users with alternate_email_1: 7015
  - Users with alternate_email_2: 6505
  - Users with country: 8776

Analyzing married couples with VH matching...
  Total couples: 424
  - Both matched: 287
  - Only A matched: 36
  - Only B matched: 56
  - Neither matched: 16
  - Auto-merged (A): 5
  - Auto-merged (B): 6
  - Conflicts (A): 14
  - Conflicts (B): 16
  Total couple matches: 395
  Total conflicts: 30

Generating married couples CSV files...
  Written 395 records to /Users/edoshor/projects/vh/wsp/analysis/married_couples_mapping.csv
  Written 65 conflict rows to /Users/edoshor/projects/vh/wsp/analysis/married_couples_conflicts.csv

  Match status summary:
    - both_matched: 287 (72.66%)
    - only_a_matched: 36 (9.11%)
    - only_b_matched: 56 (14.18%)
    - neither_matched: 16 (4.05%)


================================================================================
MARRIED COUPLES ANALYSIS REPORT
================================================================================

Total married couples analyzed: 424

--------------------------------------------------------------------------------
VH MATCHING STATUS
--------------------------------------------------------------------------------

Couples with both spouses matched to VH: 287
Couples with only spouse A matched: 36
Couples with only spouse B matched: 56
Couples with neither matched: 16
Couples with conflicts: 29

--------------------------------------------------------------------------------
MATCH TYPE BREAKDOWN
--------------------------------------------------------------------------------

Spouse A match types:
  - primary_to_primary: 318
  - primary_to_alt: 4
  - alt_to_primary: 1
  - alt_to_alt: 0

Spouse B match types:
  - primary_to_primary: 340
  - primary_to_alt: 3
  - alt_to_primary: 0
  - alt_to_alt: 0

--------------------------------------------------------------------------------
CONFLICT ANALYSIS
--------------------------------------------------------------------------------

Total conflict records: 30
  - Spouse A conflicts: 14
  - Spouse B conflicts: 16

Example conflicts:
  Relationship 14157, Spouse B: ארז בן ציון (erezbenzion@gmail.com)
    → VH User f118bd1a-410a-435b-982a-f938473b9005: None None (ormekif@gmail.com)
    → VH User e8a24106-07b7-4a75-9364-e2db9553abd6: erez ben zion (erezbenzion@gmail.com)
  Relationship 14158, Spouse B: רותם איגומנוב (rotem.yerushalmi@gmail.com)
    → VH User 2142c207-240b-48af-b3b1-6169521eda9b: rotem igumnov (igrotem93@gmail.com)
    → VH User 02fd3f06-f427-4f7c-97c4-44a691c76139: None None (rotem.yerushalmi@gmail.com)
  Relationship 14200, Spouse B: דודי אהרוני (dudi@kab.co.il)
    → VH User 77143daa-97cd-40ef-8fe9-3d5a7b9cfa68: Dudi Aharoni (dudi.aha@gmail.com)
    → VH User dd74e5d9-7ae2-4673-9960-f6d251b8dee3: None None (dudi@kab.co.il)

--------------------------------------------------------------------------------
IMPORT SUMMARY
--------------------------------------------------------------------------------

Couples ready for import (at least one spouse matched): 379
Couples with both spouses matched: 287
Couples needing conflict resolution: 29
Couples with no VH matches: 16

================================================================================
Report generated successfully!
================================================================================

================================================================================
Analysis completed successfully!
================================================================================

CSV files generated:
  - /Users/edoshor/projects/vh/wsp/analysis/married_couples_mapping.csv
  - /Users/edoshor/projects/vh/wsp/analysis/married_couples_conflicts.csv
