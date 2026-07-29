-- Runtime fields Studio merges with control-plane instance metadata
ALTER TABLE instances ADD COLUMN ports_json TEXT;
ALTER TABLE instances ADD COLUMN k8s_namespace TEXT;
ALTER TABLE instances ADD COLUMN k8s_degraded INTEGER;
ALTER TABLE instances ADD COLUMN k8s_message TEXT;
