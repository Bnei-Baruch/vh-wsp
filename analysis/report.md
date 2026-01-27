================================================================================
Country and Email Matching Analysis
================================================================================

Connecting to databases...
  ✓ Connected to civi_staging
  ✓ Connected to replica_profiles

To-do 1: Extract Country Data from `civi_staging` - In Progress
  Extracted 78525 country records from civi_staging
  - Custom field records: 12894
  - Built-in schema records: 65584
To-do 1: Extract Country Data from `civi_staging` - Completed

To-do 2: Extract Email Data from `civi_staging` - In Progress
  Extracted 59861 email records from civi_staging
  - Primary emails: 59310
  - Alternative emails: 551
To-do 2: Extract Email Data from `civi_staging` - Completed

Extracting CiVi contact names and primary emails...
  Extracted 63278 contact records from civi_staging

To-do 3: Extract Profile Data from `replica_profiles` - In Progress
  Extracted 16593 profile records from replica_profiles
  - Users with primary_email: 16593
  - Users with alternate_email_1: 7015
  - Users with alternate_email_2: 6505
  - Users with country: 8776
  - Users with first_name: 6482
  - Users with last_name: 6480
To-do 3: Extract Profile Data from `replica_profiles` - Completed

Fetching valid country codes from country_list...
  Found 241 valid country codes

To-do 4: Perform Email Matching Analysis - In Progress
To-do 4: Perform Email Matching Analysis - Completed

To-do 5: Perform Country Matching Analysis - In Progress
To-do 5: Perform Country Matching Analysis - Completed

To-do 7: Perform User-Country Comparison Analysis - In Progress
  Matched 9,537 user pairs by email
  - Missing in both: 352
  - Missing only in civi: 504
  - Missing only in vh: 2,427
  - Exists and equals: 5,910
  - Exists but different: 344
To-do 7: Perform User-Country Comparison Analysis - Completed

Building VH-centric user mapping...
  Total VH users: 16,593
  - With match: 9,395
  - No match: 7,198
  - Unique match (single contact): 4,599
  - Auto-merged (same country): 4,265
  - True conflicts (diff country): 531
  Total unique match records: 8,864
  Conflict match records: 3,039

Generating sync CSV files...
  Written 8,864 records to /Users/edoshor/projects/vh/wsp/analysis/user_mapping.csv
  Written 3,039 records to /Users/edoshor/projects/vh/wsp/analysis/user_mapping_conflicts.csv

  Country status summary (unique matches):
    - missing_in_both: 320 (3.61%)
    - missing_in_civi: 323 (3.64%)
    - missing_in_vh: 2,517 (28.40%)
    - equals: 5,511 (62.17%)
    - different: 193 (2.18%)

  Match type summary (unique matches):
    - primary_to_primary: 8,514 (96.05%)
    - primary_to_alt: 16 (0.18%)
    - alt_to_primary: 334 (3.77%)
    - alt_to_alt: 0 (0.00%)

To-do 6: Generate Final Report - In Progress

================================================================================
COUNTRY AND EMAIL MATCHING ANALYSIS REPORT
================================================================================

--------------------------------------------------------------------------------
EMAIL MATCHING STATISTICS
--------------------------------------------------------------------------------

Primary Email Matching:
  - CiviCRM Primary → Replica Primary Email: 9,027
  - CiviCRM Primary → Replica Alternate Email 1: 1,652
  - CiviCRM Primary → Replica Alternate Email 2: 732
  - Total Primary Email Matches: 11,411

Alternative Email Matching:
  - CiviCRM Alternative → Replica Primary Email: 148
  - CiviCRM Alternative → Replica Alternate Email 1: 32
  - CiviCRM Alternative → Replica Alternate Email 2: 13
  - Total Alternative Email Matches: 193

Overall Email Matching:
  - Total Unique CiviCRM Emails: 34,689
  - Total Unique Replica Emails: 18,351
  - Total Unique Matches: 9,559
  - Match Rate: 27.56%

Unmatched Emails:
  - Unmatched CiviCRM Primary Emails: 25,049
  - Unmatched CiviCRM Alternative Emails: 365
  - Total Unmatched CiviCRM Emails: 25,414

--------------------------------------------------------------------------------
COUNTRY MATCHING STATISTICS
--------------------------------------------------------------------------------

Total Unique Countries in CiviCRM: 179
Total Unique Countries in Replica: 131
Matched Countries: 120
Unmatched in CiviCRM (not in Replica): 59
Unmatched in Replica (not in CiviCRM): 11
Valid Countries (in country_list): 175
Invalid Countries (not in country_list): 4

Country Coverage in Replica:
  - Current Users with Country: 8,776
  - Current Users without Country: 7,817
  - Total Users: 16,593

--------------------------------------------------------------------------------
FULL COUNTRY DISTRIBUTION IN CIVICRM
(All countries sorted by contact count, descending)
--------------------------------------------------------------------------------
  ✓ ✓ IL: 58,086 contacts (custom:7305, builtin:50781)
  ✓ ✓ US: 5,599 contacts (custom:713, builtin:4886)
  ✓ ✓ RU: 3,361 contacts (custom:938, builtin:2423)
  ✓ ✓ UA: 1,995 contacts (custom:658, builtin:1337)
  ✓ ✓ BR: 1,731 contacts (custom:69, builtin:1662)
  ✓ ✓ DE: 677 contacts (custom:287, builtin:390)
  ✓ ✓ IT: 475 contacts (custom:220, builtin:255)
  ✓ ✓ KZ: 467 contacts (custom:213, builtin:254)
  ✓ ✓ TR: 420 contacts (custom:185, builtin:235)
  ✓ ✓ CA: 376 contacts (custom:151, builtin:225)
  ✓ ✓ MX: 371 contacts (custom:150, builtin:221)
  ✓ ✓ ES: 319 contacts (custom:144, builtin:175)
  ✓ ✓ LT: 303 contacts (custom:120, builtin:183)
  ✓ ✓ CL: 266 contacts (custom:91, builtin:175)
  ✓ ✓ BG: 249 contacts (custom:88, builtin:161)
  ✓ ✓ GB: 242 contacts (custom:113, builtin:129)
  ✓ ✓ LV: 201 contacts (custom:84, builtin:117)
  ✓ ✓ BY: 200 contacts (custom:86, builtin:114)
  ✓ ✓ CZ: 180 contacts (custom:91, builtin:89)
  ✓ ✓ CO: 179 contacts (custom:73, builtin:106)
  ✓ ✓ FR: 164 contacts (custom:80, builtin:84)
  ✓ ✓ NL: 143 contacts (custom:46, builtin:97)
  ✓ ✓ AU: 140 contacts (custom:73, builtin:67)
  ✓ ✓ RO: 129 contacts (custom:54, builtin:75)
  ✓ ✓ MD: 109 contacts (custom:45, builtin:64)
  ✓ ✓ AT: 104 contacts (custom:44, builtin:60)
  ✓ ✓ PL: 101 contacts (custom:60, builtin:41)
  ✓ ✓ SE: 92 contacts (custom:28, builtin:64)
  ✓ ✓ GE: 88 contacts (custom:37, builtin:51)
  ✓ ✓ EE: 83 contacts (custom:29, builtin:54)
  ✓ ✓ AR: 77 contacts (custom:29, builtin:48)
  ✓ ✓ CN: 75 contacts (custom:25, builtin:50)
  ✓ ✓ KG: 65 contacts (custom:22, builtin:43)
  ✓ ✓ CH: 57 contacts (custom:29, builtin:28)
  ✓ ✓ UZ: 55 contacts (custom:12, builtin:43)
  ✓ ✓ SK: 53 contacts (custom:21, builtin:32)
  ✓ ✓ NO: 51 contacts (custom:17, builtin:34)
  ✓ ✓ AZ: 48 contacts (custom:14, builtin:34)
  ✓ ✓ HU: 45 contacts (custom:28, builtin:17)
  ✓ ✓ BE: 42 contacts (custom:31, builtin:11)
  ✓ ✓ ZA: 40 contacts (custom:15, builtin:25)
  ✓ ✓ JP: 37 contacts (custom:14, builtin:23)
  ✓ ✓ HR: 36 contacts (custom:23, builtin:13)
  ✓ ✓ PT: 36 contacts (custom:17, builtin:19)
  ✓ ✓ IN: 34 contacts (custom:9, builtin:25)
  ✓ ✓ FI: 31 contacts (custom:15, builtin:16)
  ✓ ✓ CR: 31 contacts (custom:21, builtin:10)
  ✓ ✓ SZ: 28 contacts (custom:4, builtin:24)
  ✓ ✓ GR: 28 contacts (custom:8, builtin:20)
  ✓ ✓ EC: 27 contacts (custom:16, builtin:11)
  ✓ ✓ PE: 24 contacts (custom:5, builtin:19)
  ✓ ✓ AF: 23 contacts (custom:0, builtin:23)
  ✓ ✓ CD: 23 contacts (custom:3, builtin:20)
  ✗ ✓ AI: 21 contacts (custom:20, builtin:1)
  ✓ ✓ AE: 19 contacts (custom:6, builtin:13)
  ✓ ✓ PH: 19 contacts (custom:15, builtin:4)
  ✓ ✓ SI: 18 contacts (custom:6, builtin:12)
  ✓ ✓ SG: 17 contacts (custom:5, builtin:12)
  ✓ ✓ CG: 17 contacts (custom:0, builtin:17)
  ✓ ✓ IE: 17 contacts (custom:11, builtin:6)
  ✓ ✓ CY: 16 contacts (custom:7, builtin:9)
  ✓ ✓ RS: 16 contacts (custom:5, builtin:11)
  ✓ ✓ SV: 16 contacts (custom:2, builtin:14)
  ✓ ✓ DK: 15 contacts (custom:6, builtin:9)
  ✓ ✓ AM: 15 contacts (custom:6, builtin:9)
  ✓ ✓ NG: 14 contacts (custom:6, builtin:8)
  ✓ ✓ VE: 14 contacts (custom:12, builtin:2)
  ✓ ✓ UY: 12 contacts (custom:6, builtin:6)
  ✓ ✓ NZ: 11 contacts (custom:4, builtin:7)
  ✓ ✓ GT: 11 contacts (custom:7, builtin:4)
  ✓ ✓ GH: 10 contacts (custom:6, builtin:4)
  ✓ ✓ BW: 10 contacts (custom:4, builtin:6)
  ✓ ✓ MK: 9 contacts (custom:4, builtin:5)
  ✗ ✓ KW: 9 contacts (custom:0, builtin:9)
  ✓ ✓ BS: 9 contacts (custom:2, builtin:7)
  ✓ ✓ TH: 8 contacts (custom:5, builtin:3)
  ✓ ✓ TW: 8 contacts (custom:2, builtin:6)
  ✓ ✓ DO: 8 contacts (custom:1, builtin:7)
  ✓ ✓ TG: 8 contacts (custom:7, builtin:1)
  ✓ ✓ AL: 7 contacts (custom:0, builtin:7)
  ✓ ✓ ZW: 6 contacts (custom:2, builtin:4)
  ✓ ✓ BO: 6 contacts (custom:2, builtin:4)
  ✓ ✓ AW: 6 contacts (custom:3, builtin:3)
  ✗ ✓ BD: 6 contacts (custom:1, builtin:5)
  ✓ ✓ AO: 6 contacts (custom:0, builtin:6)
  ✓ ✓ PR: 5 contacts (custom:3, builtin:2)
  ✗ ✓ TC: 5 contacts (custom:0, builtin:5)
  ✓ ✓ ME: 5 contacts (custom:5, builtin:0)
  ✗ ⚠ UM: 5 contacts (custom:0, builtin:5)
  ✓ ✓ MA: 5 contacts (custom:0, builtin:5)
  ✓ ✓ CI: 5 contacts (custom:0, builtin:5)
  ✓ ✓ PA: 5 contacts (custom:3, builtin:2)
  ✓ ✓ VG: 5 contacts (custom:2, builtin:3)
  ✓ ✓ MR: 5 contacts (custom:0, builtin:5)
  ✓ ✓ ID: 5 contacts (custom:1, builtin:4)
  ✗ ✓ IQ: 4 contacts (custom:0, builtin:4)
  ✗ ✓ VI: 4 contacts (custom:3, builtin:1)
  ✗ ✓ BH: 4 contacts (custom:0, builtin:4)
  ✗ ✓ BA: 4 contacts (custom:1, builtin:3)
  ✓ ✓ MT: 4 contacts (custom:1, builtin:3)
  ✓ ✓ RE: 4 contacts (custom:3, builtin:1)
  ✓ ✓ BF: 4 contacts (custom:0, builtin:4)
  ✗ ✓ WF: 4 contacts (custom:0, builtin:4)
  ✗ ✓ BT: 4 contacts (custom:2, builtin:2)
  ✓ ✓ JO: 4 contacts (custom:0, builtin:4)
  ✓ ✓ MY: 4 contacts (custom:3, builtin:1)
  ✗ ✓ AQ: 4 contacts (custom:4, builtin:0)
  ✓ ✓ HN: 3 contacts (custom:2, builtin:1)
  ✓ ✓ KN: 3 contacts (custom:1, builtin:2)
  ✗ ✓ AX: 3 contacts (custom:0, builtin:3)
  ✓ ✓ KE: 3 contacts (custom:1, builtin:2)
  ✓ ✓ GN: 3 contacts (custom:1, builtin:2)
  ✓ ✓ KH: 3 contacts (custom:2, builtin:1)
  ✗ ✓ AS: 3 contacts (custom:0, builtin:3)
  ✗ ✓ NC: 3 contacts (custom:0, builtin:3)
  ✗ ✓ LR: 3 contacts (custom:0, builtin:3)
  ✗ ✓ IO: 3 contacts (custom:0, builtin:3)
  ✓ ✓ HT: 3 contacts (custom:3, builtin:0)
  ✓ ✓ ET: 3 contacts (custom:3, builtin:0)
  ✗ ⚠ CS: 3 contacts (custom:3, builtin:0)
  ✓ ✓ ML: 3 contacts (custom:3, builtin:0)
  ✗ ✓ TM: 2 contacts (custom:1, builtin:1)
  ✗ ✓ QA: 2 contacts (custom:0, builtin:2)
  ✓ ✓ CM: 2 contacts (custom:0, builtin:2)
  ✗ ✓ YE: 2 contacts (custom:1, builtin:1)
  ✗ ✓ MU: 2 contacts (custom:0, builtin:2)
  ✓ ✓ KR: 2 contacts (custom:1, builtin:1)
  ✓ ✓ EG: 2 contacts (custom:1, builtin:1)
  ✗ ✓ BM: 2 contacts (custom:2, builtin:0)
  ✓ ✓ AD: 2 contacts (custom:0, builtin:2)
  ✓ ✓ TT: 2 contacts (custom:1, builtin:1)
  ✗ ✓ BB: 2 contacts (custom:0, builtin:2)
  ✗ ✓ IS: 2 contacts (custom:1, builtin:1)
  ✗ ✓ FK: 2 contacts (custom:0, builtin:2)
  ✗ ✓ GG: 2 contacts (custom:0, builtin:2)
  ✗ ✓ HK: 2 contacts (custom:0, builtin:2)
  ✓ ✓ MO: 2 contacts (custom:2, builtin:0)
  ✗ ✓ GF: 2 contacts (custom:1, builtin:1)
  ✗ ✓ GU: 2 contacts (custom:1, builtin:1)
  ✗ ✓ IM: 2 contacts (custom:1, builtin:1)
  ✗ ✓ JE: 1 contacts (custom:1, builtin:0)
  ✓ ✓ IR: 1 contacts (custom:0, builtin:1)
  ✗ ⚠ CW: 1 contacts (custom:0, builtin:1)
  ✗ ✓ LB: 1 contacts (custom:0, builtin:1)
  ✗ ✓ TJ: 1 contacts (custom:0, builtin:1)
  ✗ ✓ DM: 1 contacts (custom:0, builtin:1)
  ✗ ✓ KP: 1 contacts (custom:0, builtin:1)
  ✗ ✓ CF: 1 contacts (custom:0, builtin:1)
  ✓ ✓ DZ: 1 contacts (custom:0, builtin:1)
  ✗ ✓ SY: 1 contacts (custom:0, builtin:1)
  ✗ ✓ CV: 1 contacts (custom:0, builtin:1)
  ✗ ✓ PY: 1 contacts (custom:0, builtin:1)
  ✗ ⚠ BQ: 1 contacts (custom:0, builtin:1)
  ✗ ✓ MP: 1 contacts (custom:0, builtin:1)
  ✗ ✓ FO: 1 contacts (custom:0, builtin:1)
  ✗ ✓ VN: 1 contacts (custom:0, builtin:1)
  ✗ ✓ VA: 1 contacts (custom:1, builtin:0)
  ✗ ✓ MZ: 1 contacts (custom:0, builtin:1)
  ✗ ✓ GS: 1 contacts (custom:1, builtin:0)
  ✗ ✓ YT: 1 contacts (custom:0, builtin:1)
  ✗ ✓ CX: 1 contacts (custom:0, builtin:1)
  ✓ ✓ MN: 1 contacts (custom:0, builtin:1)
  ✗ ✓ MV: 1 contacts (custom:0, builtin:1)
  ✗ ✓ LS: 1 contacts (custom:0, builtin:1)
  ✓ ✓ LY: 1 contacts (custom:1, builtin:0)
  ✗ ✓ PS: 1 contacts (custom:0, builtin:1)
  ✗ ✓ TK: 1 contacts (custom:0, builtin:1)
  ✗ ✓ GY: 1 contacts (custom:1, builtin:0)
  ✓ ✓ LC: 1 contacts (custom:1, builtin:0)
  ✓ ✓ GD: 1 contacts (custom:1, builtin:0)
  ✗ ✓ NU: 1 contacts (custom:0, builtin:1)
  ✓ ✓ LU: 1 contacts (custom:1, builtin:0)
  ✓ ✓ AG: 1 contacts (custom:1, builtin:0)
  ✗ ✓ NA: 1 contacts (custom:1, builtin:0)
  ✗ ✓ TZ: 1 contacts (custom:1, builtin:0)
  ✓ ✓ BJ: 1 contacts (custom:1, builtin:0)
  ✓ ✓ GP: 1 contacts (custom:1, builtin:0)
  ✗ ✓ WS: 1 contacts (custom:1, builtin:0)
  ✓ ✓ UG: 1 contacts (custom:1, builtin:0)

--------------------------------------------------------------------------------
INVALID COUNTRIES (not in country_list)
--------------------------------------------------------------------------------
  ⚠ BQ: 1 contacts
  ⚠ CS: 3 contacts
  ⚠ CW: 1 contacts
  ⚠ UM: 5 contacts

--------------------------------------------------------------------------------
UNMATCHED COUNTRIES IN CIVICRM (not found in Replica)
--------------------------------------------------------------------------------
  ✗ AI: 21 contacts
  ✗ AQ: 4 contacts
  ✗ AS: 3 contacts
  ✗ AX: 3 contacts
  ✗ BA: 4 contacts
  ✗ BB: 2 contacts
  ✗ BD: 6 contacts
  ✗ BH: 4 contacts
  ✗ BM: 2 contacts
  ✗ BQ: 1 contacts
  ✗ BT: 4 contacts
  ✗ CF: 1 contacts
  ✗ CS: 3 contacts
  ✗ CV: 1 contacts
  ✗ CW: 1 contacts
  ✗ CX: 1 contacts
  ✗ DM: 1 contacts
  ✗ FK: 2 contacts
  ✗ FO: 1 contacts
  ✗ GF: 2 contacts
  ✗ GG: 2 contacts
  ✗ GS: 1 contacts
  ✗ GU: 2 contacts
  ✗ GY: 1 contacts
  ✗ HK: 2 contacts
  ✗ IM: 2 contacts
  ✗ IO: 3 contacts
  ✗ IQ: 4 contacts
  ✗ IS: 2 contacts
  ✗ JE: 1 contacts
  ✗ KP: 1 contacts
  ✗ KW: 9 contacts
  ✗ LB: 1 contacts
  ✗ LR: 3 contacts
  ✗ LS: 1 contacts
  ✗ MP: 1 contacts
  ✗ MU: 2 contacts
  ✗ MV: 1 contacts
  ✗ MZ: 1 contacts
  ✗ NA: 1 contacts
  ✗ NC: 3 contacts
  ✗ NU: 1 contacts
  ✗ PS: 1 contacts
  ✗ PY: 1 contacts
  ✗ QA: 2 contacts
  ✗ SY: 1 contacts
  ✗ TC: 5 contacts
  ✗ TJ: 1 contacts
  ✗ TK: 1 contacts
  ✗ TM: 2 contacts
  ✗ TZ: 1 contacts
  ✗ UM: 5 contacts
  ✗ VA: 1 contacts
  ✗ VI: 4 contacts
  ✗ VN: 1 contacts
  ✗ WF: 4 contacts
  ✗ WS: 1 contacts
  ✗ YE: 2 contacts
  ✗ YT: 1 contacts

--------------------------------------------------------------------------------
USER-COUNTRY COMPARISON
(For users matched by email)
--------------------------------------------------------------------------------

Total Matched User Pairs: 9,537

Country Comparison Results:
  - Missing in both: 352 (3.69%)
  - Missing only in civi: 504 (5.28%)
  - Missing only in vh: 2,427 (25.45%)
  - Exists and equals: 5,910 (61.97%)
  - Exists but different: 344 (3.61%)

================================================================================
Report generated successfully!
================================================================================
To-do 6: Generate Final Report - Completed

================================================================================
Analysis completed successfully!
================================================================================

CSV files generated:
  - /Users/edoshor/projects/vh/wsp/analysis/user_mapping.csv
  - /Users/edoshor/projects/vh/wsp/analysis/user_mapping_conflicts.csv
