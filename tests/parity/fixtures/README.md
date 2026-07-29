# Parity fixture notes
# Table `parity_items` is created by lidb migration `011_parity_items.sql`
# Columns: id, name, owner_id, secret, created_at
# RLS: select/insert restricted to jwt sub == owner_id (service_role bypass)
