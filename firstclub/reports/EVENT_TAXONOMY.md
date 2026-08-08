# FirstClub Event Taxonomy — Install-to-First-Order Funnel

Version 1.0 | Analytics | All events include: `user_id`, `session_id`, `timestamp`, `platform`, `city`, `app_version`

---

## Acquisition Events

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `app_install` | First open after install | `channel`, `campaign_id`, `device_model` |
| `app_open` | Every cold/warm start | `is_returning`, `days_since_install` |
| `deep_link_open` | Opened via referral/campaign link | `link_type`, `referrer_id` |

## Onboarding Funnel

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `signup_start` | Phone entry screen shown | — |
| `signup_complete` | OTP verified | `method` (phone/apple/google) |
| `location_permission_prompt` | Location modal shown | — |
| `location_set` | Serviceable pin confirmed | `pincode`, `lat`, `lng`, `dark_store_id` |
| `onboarding_skip` | User skips optional step | `step_name` |

## Browse → Cart

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `catalog_view` | Home/category loaded | `category_id`, `item_count` |
| `product_view` | PDP opened | `sku_id`, `price_inr`, `in_stock` |
| `search` | Search executed | `query`, `result_count` |
| `add_to_cart` | Item added | `sku_id`, `qty`, `cart_value_inr` |
| `remove_from_cart` | Item removed | `sku_id`, `reason` |
| `stockout_view` | OOS shown on PDP | `sku_id`, `substitute_shown` |

## Checkout → First Order

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `checkout_start` | Cart → checkout | `cart_value_inr`, `item_count` |
| `address_confirm` | Delivery address confirmed | `address_type` |
| `payment_method_select` | Payment option chosen | `method` (upi/card/cod/wallet) |
| `payment_success` | Payment captured | `order_id`, `amount_inr`, `discount_inr` |
| `payment_fail` | Payment failed | `error_code`, `method` |
| `order_placed` | Order confirmed | `order_id`, `is_first_order`, `eta_min` |
| `order_delivered` | Delivery confirmed | `order_id`, `actual_delivery_min`, `rating_prompt_shown` |

## Retention & Engagement

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `push_received` | Push notification delivered | `campaign_id`, `type` |
| `push_open` | User taps push | `campaign_id`, `deep_link_target` |
| `reorder_tap` | One-tap reorder used | `order_id_ref`, `sku_count` |
| `subscription_start` | Subscribe & save activated | `sku_ids`, `frequency` |
| `review_submitted` | In-app or store review | `rating`, `theme_tags` |

## Experiment Exposure

| Event Name | Trigger | Properties |
|------------|---------|------------|
| `experiment_exposure` | User enters test bucket | `experiment_id`, `variant`, `layer` |

---

## Funnel SQL (BigQuery / Redshift)

```sql
-- Install to first order conversion (7-day window)
WITH installs AS (
  SELECT user_id, MIN(timestamp) AS install_ts
  FROM events WHERE event_name = 'app_install'
  GROUP BY 1
),
first_orders AS (
  SELECT user_id, MIN(timestamp) AS first_order_ts
  FROM events
  WHERE event_name = 'order_delivered'
    AND JSON_EXTRACT_SCALAR(properties, '$.is_first_order') = 'true'
  GROUP BY 1
)
SELECT
  COUNT(DISTINCT i.user_id) AS installs,
  COUNT(DISTINCT f.user_id) AS first_orders,
  COUNT(DISTINCT f.user_id) * 1.0 / COUNT(DISTINCT i.user_id) AS conversion_rate
FROM installs i
LEFT JOIN first_orders f
  ON i.user_id = f.user_id
  AND f.first_order_ts <= TIMESTAMP_ADD(i.install_ts, INTERVAL 7 DAY);
```

## Naming Conventions

- `snake_case` event names
- Properties in `lower_snake_case`
- Currency in INR as `_inr` suffix
- Booleans as `is_` / `has_` prefix
