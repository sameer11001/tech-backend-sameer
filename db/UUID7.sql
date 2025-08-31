CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid LANGUAGE SQL AS $$
SELECT (
  lpad(to_hex((EXTRACT(EPOCH FROM clock_timestamp())*1000)::bigint >> 16), 8,  '0') || '-' ||
  lpad(to_hex(((EXTRACT(EPOCH FROM clock_timestamp())*1000)::bigint & 0xFFFF)::int), 4, '0') || '-' ||
  lpad(to_hex(0x7000 | (floor(random()*4096)::int)),                               4,  '0') || '-' ||  
  lpad(to_hex(0x8000 | (floor(random()*16384)::int)),                              4,  '0') || '-' ||   
  lpad(to_hex(floor(random()*281474976710656)::bigint),                           12,  '0')
)::uuid;
$$;
