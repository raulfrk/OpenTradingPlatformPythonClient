from typing import Any

import pandas as pd


class Base:
    @classmethod
    def list_to_dataframe(cls, entities: list["Any"]):
        """Convert a list of entities to a DataFrame."""
        data = [entity.__dict__ for entity in entities]

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        # Convert timestamp to datetime and set it as the index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # Drop the original "timestamp" column
        df.drop(columns=['timestamp'], inplace=True, errors="ignore")

        return df
