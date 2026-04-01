

-- name: get_client_timeline
WITH client_bounds AS (
    SELECT 
        MIN(date) as start_date, 
        MAX(date) as end_date
    FROM daily_transactions 
    WHERE client_name = :client_name
)
(
    SELECT 
        id, 
        symbol, 
        date AS event_date, 
        'Transaction' AS source, 
        'daily_transactions' AS collection_name, 
        created, 
        updated, 
        jsonb_build_object('trn_no', trn_no, 'qty', qty) AS metadata
    FROM daily_transactions 
    WHERE client_name = :client_name

    UNION ALL

    SELECT 
        ca.id, 
        ca.symbol, 
        ca.book_close_date AS event_date, 
        ca.corporate_action_type AS source, 
        'corporate_actions' AS collection_name, 
        ca.created_at AS created, 
        ca.updated_at AS updated, 
        jsonb_build_object('bonus_pct', ca.bonus_pct) AS metadata
    FROM corporate_actions ca, client_bounds cb
    WHERE ca.book_close_date BETWEEN cb.start_date AND cb.end_date
)
ORDER BY event_date ASC;