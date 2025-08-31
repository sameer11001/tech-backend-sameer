CREATE OR REPLACE PROCEDURE broadcast_messaging(
    IN  p_contact_phone        TEXT,
    IN  p_country_code_phone   TEXT,
    IN  p_business_phone       TEXT,
    IN  p_whatsapp_message_id  TEXT,
    IN  p_user_id              UUID,
    OUT p_conversation_id      UUID,
    OUT p_message_id           UUID
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_client_id        UUID;
    v_contact_id       UUID;
    v_team_id          UUID;
    v_assignment_id    UUID;
    v_contact_source   TEXT := 'WHATSAPP';
    v_contact_name     TEXT;
    ts_now             TIMESTAMP;
BEGIN
    ts_now := NOW() AT TIME ZONE 'UTC';

    SELECT client_id INTO v_client_id
    FROM business_profile
    WHERE phone_number = p_business_phone
    LIMIT 1;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Business profile not found for phone %', p_business_phone;
    END IF;

    SELECT c.id, c.contact_id INTO p_conversation_id, v_contact_id
    FROM conversations c
    JOIN contacts ct ON c.contact_id = ct.id
    WHERE ct.phone_number = p_contact_phone
      AND ct.client_id = v_client_id
    LIMIT 1;

    IF FOUND THEN
        p_message_id := uuid_generate_v7();
        INSERT INTO messages (
            id, created_at, updated_at,
            message_type, message_status,
            whatsapp_message_id, is_from_contact,
            member_id, contact_id, conversation_id
        ) VALUES (
            p_message_id, ts_now, ts_now,
            'template', 'sent',
            p_whatsapp_message_id, FALSE,
            p_user_id, v_contact_id, p_conversation_id
        );
        RETURN;
    END IF;

    SELECT id INTO v_contact_id
    FROM contacts
    WHERE phone_number = p_contact_phone
      AND client_id = v_client_id
    LIMIT 1;

    IF NOT FOUND THEN
        v_contact_name := p_country_code_phone || p_contact_phone;
        v_contact_id := uuid_generate_v7();
        INSERT INTO contacts (
            id, created_at, updated_at,
            name, country_code, phone_number, source,
            status, allow_broadcast, allow_sms,
            client_id
        ) VALUES (
            v_contact_id, 
            ts_now, 
            ts_now,
            v_contact_name,
            p_country_code_phone,
            p_contact_phone,
            v_contact_source,
            'valid',
            TRUE,
            TRUE,
            v_client_id
        );
    END IF;

    SELECT id INTO v_assignment_id
    FROM assignments
    WHERE user_id = p_user_id
    LIMIT 1;


    p_conversation_id := uuid_generate_v7();
    INSERT INTO conversations (
        id, created_at, updated_at,
        status, contact_id, assignment_id, client_id,
        is_open, chatbot_triggered
    ) VALUES (
        p_conversation_id, ts_now, ts_now,
        'BROADCAST', v_contact_id, v_assignment_id, v_client_id,
        FALSE, TRUE
    );

    SELECT id INTO v_team_id
    FROM teams
    WHERE client_id = v_client_id
      AND is_default = TRUE
    LIMIT 1;

    IF FOUND THEN
        INSERT INTO conversation_team_link (id,created_at , updated_at, conversation_id, team_id)
        VALUES (uuid_generate_v7(), ts_now, ts_now, p_conversation_id, v_team_id)
        ON CONFLICT DO NOTHING; 
    END IF;

    p_message_id := uuid_generate_v7();
    INSERT INTO messages (
        id, created_at, updated_at,
        message_type, message_status,
        whatsapp_message_id, is_from_contact,
        member_id, contact_id, conversation_id
    ) VALUES (
        p_message_id, ts_now, ts_now,
        'template', 'sent',
        p_whatsapp_message_id, FALSE,
        p_user_id, v_contact_id, p_conversation_id
    );
END;
$$;
