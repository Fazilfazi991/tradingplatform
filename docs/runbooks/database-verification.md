# PostgreSQL migration verification

This host lacked Docker, `psql` and Supabase CLI during Batch 1, so database-runtime verification is
an explicit condition. Before any deployment:

1. Use PostgreSQL 15+ (hosted Supabase current supported version or local instance).
2. Apply `infra/migrations/0001_prediction_data_foundation.sql` in a disposable database.
3. Verify all tables are in `verified_edge`, not `public`.
4. Confirm `anon` and `authenticated` cannot select any table.
5. Insert a valid raw/canonical row, then verify UPDATE and DELETE fail.
6. Seal a dataset, then verify UPDATE/DELETE fail while an unsealed dataset can be completed.
7. Attempt invalid OHLC, negative volume, duplicate raw identity and causal-time violations.
8. Run Supabase database advisors and resolve all findings before committing a hosted migration.

Do not expose the schema through the Data API and do not use a service-role key in a browser.

