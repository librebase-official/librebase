#!/usr/bin/env node
/**
 * Seed the postgrest-js test schema data via REST (backend-agnostic).
 * Usage: node seed-rest.mjs <api-url> [anon-key]
 * Loads /tmp/pg-seed-portable.sql into the backend through its Data API.
 */
import { createClient } from "@supabase/supabase-js";

const API = process.argv[2] ?? "http://127.0.0.1:54325";
const ANON = process.argv[3] ?? "anon";
const sb = createClient(API, ANON);

const seedRows = {
  users: [
    { username: "supabot", status: "ONLINE", age_range: "[1,2)", catchphrase: "fat cat", data: null },
    { username: "kiwicopple", status: "OFFLINE", age_range: "[25,35)", catchphrase: "cat bat", data: null },
    { username: "awailas", status: "ONLINE", age_range: "[25,35)", catchphrase: "bat rat", data: null },
    { username: "dragarcia", status: "ONLINE", age_range: "[20,30)", catchphrase: "rat fat", data: null },
    { username: "jsonuser", status: "ONLINE", age_range: "[20,30)", catchphrase: "json test", data: { foo: { bar: { nested: "value" }, baz: "string value" } } },
  ],
  channels: [
    { slug: "public" }, { slug: "random" }, { slug: "other" },
  ],
  messages: [
    { message: "Hello World 👋", channel_id: 1, username: "supabot" },
    { message: "Perfection is attained, not when there is nothing more to add, but when there is nothing left to take away.", channel_id: 2, username: "supabot" },
    { message: "Some message on channel without details", channel_id: 3, username: "supabot" },
    { message: "Some message on channel without details", channel_id: 3, username: "supabot" },
  ],
  channel_details: [
    { id: 1, details: "Details for public channel" },
    { id: 2, details: "Details for random channel" },
  ],
  user_profiles: [
    { id: 1, username: "supabot" },
    { id: 2, username: null },
  ],
  best_friends: [
    { id: 1, first_user: "supabot", second_user: "kiwicopple", third_wheel: "awailas" },
    { id: 2, first_user: "supabot", second_user: "awailas", third_wheel: null },
  ],
  collections: [
    { id: 1, description: "Root Collection", parent_id: null },
    { id: 2, description: "Child of Root", parent_id: 1 },
    { id: 3, description: "Another Child of Root", parent_id: 1 },
    { id: 4, description: "Grandchild", parent_id: 2 },
    { id: 5, description: "Sibling of Grandchild", parent_id: 2 },
    { id: 6, description: "Child of Another Root", parent_id: 3 },
  ],
  lab: [
    { id: 1, name: "Main Board", type: "board", parent: null, main: null },
    { id: 2, name: "First Task", type: "task", parent: 1, main: null },
  ],
  products: [
    { id: 1, name: "Laptop", description: "High-performance laptop", price: 999.99 },
    { id: 2, name: "Smartphone", description: "Latest model smartphone", price: 699.99 },
    { id: 3, name: "Headphones", description: "Noise-cancelling headphones", price: 199.99 },
  ],
  categories: [
    { id: 1, name: "Electronics", description: "Electronic devices and gadgets" },
    { id: 2, name: "Computers", description: "Computer and computer accessories" },
    { id: 3, name: "Audio", description: "Audio equipment" },
  ],
  product_categories: [
    { product_id: 1, category_id: 1 },
    { product_id: 1, category_id: 2 },
    { product_id: 2, category_id: 1 },
    { product_id: 3, category_id: 1 },
    { product_id: 3, category_id: 3 },
  ],
  shops: [
    { id: 1, address: "1369 Cambridge St", shop_geom: "SRID=4326;POINT(-71.10044 42.373695)" },
  ],
  hotel: [
    { id: 1, name: "Sunset Resort" },
    { id: 2, name: "Mountain View Hotel" },
    { id: 3, name: "Beachfront Inn" },
    { id: 4, name: null },
  ],
  booking: [
    { id: 1, hotel_id: 1 }, { id: 2, hotel_id: 1 }, { id: 3, hotel_id: 2 },
    { id: 4, hotel_id: null }, { id: 5, hotel_id: 3 }, { id: 6, hotel_id: 1 },
    { id: 7, hotel_id: null }, { id: 8, hotel_id: 4 },
  ],
  users_audit: [
    { id: 1, previous_value: 42 }, { id: 2, previous_value: 42 }, { id: 3, previous_value: 42 },
    { id: 4, previous_value: 42 }, { id: 5, previous_value: 42 },
  ],
  cornercase: [
    { id: 1, array_column: ["test", "one"] },
    { id: 2, array_column: ["another"] },
    { id: 3, array_column: ["test2"] },
  ],
};

let failed = 0;
for (const [table, rows] of Object.entries(seedRows)) {
  for (const row of rows) {
    const { error } = await sb.from(table).insert(row);
    if (error) {
      failed++;
      console.log(`  SEED FAIL ${table}: ${error.message}`);
    }
  }
}
console.log(`seed complete: ${failed} insert errors`);
process.exit(failed ? 1 : 0);
