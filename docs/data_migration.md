# Migrating Document Data Between Machines

This guide copies every processed document from the **home machine** (database `udp`) into the **office machine** (database `rfp_analyzer`) without deleting existing records.

## 1. Export data on the home machine

```bash
cd /home/stormy/dev-workspace/rfp_analyzer

pg_dump -h localhost -U storm -d udp \
  --data-only --inserts \
  -t document \
  -t section \
  -t chunk \
  -t trait \
  -t processingjob \
  > rfp_append.sql
```

> Enter the `storm` database password if prompted.

## 2. Fix table-name difference

The office database uses `processing_job`. Replace the table name in the dump:

```bash
sed -i 's/processingjob/processing_job/g' rfp_append.sql
```

Use a different output file if you prefer not to edit in place.

## 3. Copy the SQL file to the office machine

```bash
scp rfp_append.sql office-user@office-host:/home/office-user/rfp_append.sql
```

Adjust the host/path to match your setup.

## 4. Load the dump on the office machine (psql)

```bash
psql -h localhost -U storm -d rfp_analyzer
```

Inside the psql prompt, run:

```sql
BEGIN;
SET session_replication_role = replica;
\i /home/office-user/rfp_append.sql
SET session_replication_role = DEFAULT;
COMMIT;
```

Disabling triggers/foreign keys temporarily avoids issues with the self-referencing `section` table.

## 5. Loading via pgAdmin (optional)

1. Open pgAdmin → connect to `rfp_analyzer` → Query Tool.
2. Paste:
   ```sql
   BEGIN;
   SET session_replication_role = replica;
   -- contents inserted here
   SET session_replication_role = DEFAULT;
   COMMIT;
   ```
3. Use **File → Open File…** to insert `rfp_append.sql` between the two `SET` lines.
4. Click Execute (lightning icon).

## 6. Verify the import

```sql
SELECT count(*) FROM document;
SELECT count(*) FROM section;
```

Compare counts with the home database or spot-check a known document ID.

## 7. Reset sequences (if using integers)

Most tables use UUIDs, so this is usually unnecessary. For integer sequences:

```sql
SELECT setval('documents_id_seq', (SELECT max(id) FROM document));
```

Replace names as needed.

## 8. Clean up

Delete the SQL file after confirming the data arrived:

```bash
rm /home/office-user/rfp_append.sql
```

Repeat the same steps whenever you need to append a new batch of processed documents.

