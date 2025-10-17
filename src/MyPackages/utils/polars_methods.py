import polars as pl

#A function to replace a row in a dataframe de Polars
def replace_row(df: pl.DataFrame, row_idx: int, values: dict, *args) -> pl.DataFrame:
    """
    Returns a new Poler Dataframe with the `Row_idx` row replaced by the` Values` values.
    If the index does not exist, add the row at the end.
    """
    #Build the new row, using the given or original values ​​if they are not specified
    new_row = pl.DataFrame({
        col: [values.get(col, df[row_idx, col] if row_idx < df.height else None)]
        for col in df.columns
    })
    if df.height > row_idx:
        #Replace the row at the Row_idx position
        return (
            df.slice(0, row_idx)
            .vstack(new_row)
            .vstack(df.slice(row_idx + 1))
        )
    else:
        #If the index does not exist, add the row at the end
        return df.vstack(new_row)