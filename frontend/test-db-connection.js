/**
 * Test PostgreSQL connection from Node.js
 */

const { Client } = require('pg');

const DATABASE_URL = 'postgresql://neondb_owner:npg_zQc6IsjDU5MH@ep-delicate-cherry-ag24bs3q-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require';

async function testConnection() {
  const client = new Client({
    connectionString: DATABASE_URL,
  });

  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('✓ Connected successfully!');

    console.log('\nTesting query...');
    const result = await client.query('SELECT NOW()');
    console.log('✓ Query successful:', result.rows[0]);

    console.log('\nChecking Better Auth tables...');
    const tables = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name IN ('user', 'session', 'account', 'verification')
      ORDER BY table_name;
    `);
    console.log('✓ Found tables:', tables.rows.map(r => r.table_name));

  } catch (error) {
    console.error('✗ Error:', error.message);
    console.error('Full error:', error);
  } finally {
    await client.end();
  }
}

testConnection();
