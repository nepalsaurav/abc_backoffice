DROP FUNCTION IF EXISTS generate_client_holdings(TEXT);

CREATE OR REPLACE FUNCTION generate_client_holdings(p_client_name TEXT)
RETURNS TABLE (
    h_symbol TEXT,
    h_total_qty NUMERIC,
    h_provisional_qty NUMERIC,
    h_wacc NUMERIC,
    h_total_investment NUMERIC
) AS $$
DECLARE
    r RECORD;
    v_gross_amount NUMERIC;
    v_net_amount NUMERIC;
    v_current_wacc NUMERIC;
    v_total_held NUMERIC;
    v_action_qty NUMERIC;
    v_action_cost NUMERIC;
    v_base_price NUMERIC := 100;
    v_is_provisional BOOLEAN;
BEGIN
    -- 1. Setup Temporary Table for WACC/Balance
    DROP TABLE IF EXISTS temp_wacc;
    CREATE TEMP TABLE temp_wacc (
        t_symbol TEXT PRIMARY KEY,
        t_qty NUMERIC DEFAULT 0,      
        t_cost NUMERIC DEFAULT 0,    
        t_balance NUMERIC DEFAULT 0, 
        t_provisional NUMERIC DEFAULT 0 
    );

    -- 2. Processing Loop
    FOR r IN (
        WITH client_bounds AS (
            SELECT MIN(date) as start_date, MAX(date) as end_date
            FROM daily_transactions 
            WHERE client_name = p_client_name
        )
        SELECT 
            symbol, date AS event_date, 'Transaction' AS source, trn_type, qty, rate,
            (COALESCE(broker_commission,0)+COALESCE(sebo_commission,0)+COALESCE(nepse_commission,0)+COALESCE(dp_charge,0)+COALESCE(regulatory_fee,0)) as fees,
            NULL AS corporate_action_type, NULL::DATE AS listing_date, 0 AS bonus_pct, 0 AS right_share_pct
        FROM daily_transactions 
        WHERE client_name = p_client_name

        UNION ALL

        SELECT 
            ca.symbol, COALESCE(ca.listing_date, ca.book_close_date) AS event_date, 'corporate_actions' AS source, NULL, 0, 0, 0,
            ca.corporate_action_type, ca.listing_date, COALESCE(ca.bonus_pct,0), COALESCE(ca.right_share_pct,0)
        FROM corporate_actions ca, client_bounds cb 
        WHERE ca.book_close_date BETWEEN cb.start_date AND cb.end_date
        ORDER BY event_date ASC
    )
    LOOP
        -- Use ON CONFLICT to initialize the symbol row
        INSERT INTO temp_wacc (t_symbol) VALUES (r.symbol) ON CONFLICT DO NOTHING;
        
        -- Nepali Market Base Price Rule
        IF r.symbol = 'SHL' THEN v_base_price := 10; ELSE v_base_price := 100; END IF;

        IF r.source = 'Transaction' THEN
            IF r.trn_type = 'buy' THEN
                v_net_amount := (r.qty * r.rate) + r.fees;
                UPDATE temp_wacc 
                SET t_qty = t_qty + r.qty, 
                    t_cost = t_cost + v_net_amount, 
                    t_balance = t_balance + r.qty 
                WHERE t_symbol = r.symbol;

            ELSIF r.trn_type = 'sell' THEN
                -- Calculate current WACC before reducing quantity
                SELECT (t_cost / NULLIF(t_qty, 0)) INTO v_current_wacc 
                FROM temp_wacc WHERE t_symbol = r.symbol;
                
                v_current_wacc := COALESCE(v_current_wacc, v_base_price);

                -- Update the pool: Sell always leaves WACC unchanged
                UPDATE temp_wacc 
                SET t_balance = t_balance - r.qty,
                    t_qty = GREATEST(t_qty - r.qty, 0),
                    t_cost = CASE WHEN (t_qty - r.qty) <= 0 THEN 0 ELSE (t_qty - r.qty) * v_current_wacc END
                WHERE t_symbol = r.symbol;
            END IF;

        ELSIF r.source = 'corporate_actions' AND r.corporate_action_type IN ('bonus','right_share') THEN
            SELECT t_balance INTO v_total_held FROM temp_wacc WHERE t_symbol = r.symbol;
            CONTINUE WHEN COALESCE(v_total_held, 0) <= 0;

            v_is_provisional := (r.listing_date IS NULL);
            v_action_qty := FLOOR(v_total_held * (CASE WHEN r.corporate_action_type = 'bonus' THEN r.bonus_pct ELSE r.right_share_pct END / 100.0));
            
            IF v_action_qty > 0 THEN
                IF v_is_provisional THEN
                    UPDATE temp_wacc 
                    SET t_balance = t_balance + v_action_qty,
                        t_provisional = t_provisional + v_action_qty
                    WHERE t_symbol = r.symbol;
                ELSE
                    -- Listed: Affects WACC (usually base price Rs 100/10)
                    UPDATE temp_wacc 
                    SET t_balance = t_balance + v_action_qty,
                        t_qty = t_qty + v_action_qty, 
                        t_cost = t_cost + (v_action_qty * v_base_price) 
                    WHERE t_symbol = r.symbol;
                END IF;
            END IF;
        END IF;
    END LOOP;

    -- 3. Output results
    RETURN QUERY
    SELECT 
        t_symbol, 
        t_balance, 
        t_provisional, 
        ROUND(COALESCE((t_cost / NULLIF(t_qty, 0)), 100), 4), 
        ROUND(t_cost, 4)
    FROM temp_wacc
    WHERE t_balance > 0;

    DROP TABLE IF EXISTS temp_wacc;
END;
$$ LANGUAGE plpgsql;

SELECT * FROM generate_client_holdings('LATA CHAUDHARY (LC456959)');