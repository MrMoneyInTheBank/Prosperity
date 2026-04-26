import polars as pl


def generate_inventory_df(trader: str, trades_data: pl.DataFrame) -> pl.DataFrame:
    return (
        trades_data.sort("timestamp")
        .with_columns(
            inventory_change=pl.when(pl.col("buyer") == trader)
            .then(pl.col("quantity"))
            .when(pl.col("seller") == trader)
            .then(-pl.col("quantity"))
            .otherwise(0)
        )
        .with_columns(
            # Running total of the changes
            inventory=pl.col("inventory_change").cum_sum()
        )
        .select(["timestamp", "inventory"])
    )
