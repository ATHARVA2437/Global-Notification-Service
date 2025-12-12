-- docs/sql/rls_example.sql
-- Enable RLS and set a policy that forces rows to match current_setting('app.current_project')
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_isolation ON notifications
  USING (project_id::text = current_setting('app.current_project', true)::text);

-- Usage from your application session (SQLAlchemy):
-- After authenticating request for project_id '1111-...':
-- EXECUTE: SET LOCAL app.current_project = '11111111-1111-1111-1111-111111111111';
-- Then any SELECT/INSERT/UPDATE will be filtered by the RLS policy above.
