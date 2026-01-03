# Dataset Dictionary: Price Metrics Reference

This document provides a comprehensive reference for the 11 distinct price metrics currently stored in `fact_precios`. These metrics are sourced from **Portal de Dades (Ayuntamiento de Barcelona)** and **Idealista**, providing a rich, multi-dimensional view of the real estate market.

## Summary Table

| Metric Type           | Transaction Stage | Property Category      | Unit       | Data Source                 | Dataset ID                  | Description                                                           |
| :-------------------- | :---------------- | :--------------------- | :--------- | :-------------------------- | :-------------------------- | :-------------------------------------------------------------------- |
| **Sale: Avg. m²**     | Transacted        | All                    | €/m²       | Portal de Dades             | `bxtvnxvukh`                | Average price per m² for all actual sales transactions.               |
| **Sale: Unit Price**  | Transacted        | All                    | €/unit     | Portal de Dades             | `hostlmjrdo`                | Average total price per housing unit sold.                            |
| **Sale: By Type**     | Transacted        | New vs. Second-hand    | €/m²       | Portal de Dades             | `mrslyp5pcq`                | Average price per m² segmented by property type.                      |
| **Sale: By Age**      | Transacted        | By Year Built          | €/m²       | Portal de Dades             | `idjhkx1ruj`                | Average price per m² segmented by construction year of the building.  |
| **Sale: Reg. m²**     | Registered        | All                    | €/m²       | Portal de Dades             | `u25rr7oxh6`                | Average price per m² from the property register records.              |
| **Sale: Reg. Unit**   | Registered        | All                    | €/unit     | Portal de Dades             | `la6s9fp57r`                | Average total price per unit from the property register records.      |
| **Sale: Reg. State**  | Registered        | New vs. Used           | Both       | Portal de Dades             | `cq4causxvu` / `9ap8lewvtt` | Registered prices segmented by housing state (New/Used).              |
| **Sale: Offer Price** | Listed/Offer      | Second-hand            | €/m²       | Portal de Dades / Idealista | `bhl3ulphi5`                | Current average asking price for second-hand properties.              |
| **Rental: Monthly**   | Contracted        | All                    | €/month    | Portal de Dades             | `b37xv8wcjh`                | Average monthly rent for newly signed contracts.                      |
| **Rental: m²**        | Contracted        | All                    | €/m²/month | Portal de Dades             | `5ibudgqbrb`                | Average rent per m² for newly signed contracts.                       |
| **Rental: Advanced**  | Contracted        | By Category/Percentile | Both       | Portal de Dades             | `4waxpjj3uo` / `jc3tvqfyum` | Detailed rental prices by property type and statistical distribution. |

## Data Interpretation Guide

### 1. Transacted vs. Registered vs. Offer

- **Transacted**: Prices reflecting actual closed deals reported by decentralized sources.
- **Registered**: Formal records from the property register (often includes a time lag but is the legal truth).
- **Offer**: Current market "asking prices" from portals like Idealista. These are usually higher than final transaction prices.

### 2. Unit vs. Surface (m²)

- **Unit Price**: Total cost of a home. Useful for understanding entry-level budget requirements in different barrios.
- **Price per m²**: Standardized metric for comparing value regardless of home size. Essential for valuation and investment analysis.

### 3. Segmentation (Type/Age/State)

- **New vs. Second-hand**: Essential for understanding the premium on new developments vs. the resilience of existing stock.
- **Construction Year**: Helps identify areas with older, potentially renovatable stock vs. modern high-efficiency areas.

## How to use in Dashboard

Users can toggle between these metrics in the **Advanced Analytics** or **Market Cockpit** filters to see how different indicators behave in the same neighborhood. For example, a high gap between _Offer Price_ and _Transacted Price_ may indicate a cooling market or high negotiation room.

---

_Last updated: January 2026_
