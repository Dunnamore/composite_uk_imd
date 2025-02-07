"""
Scotish, Welsh and Northern Irish Indexes do not pubically publish the raw score in the same way.
This has to be recreated following the published methodology formother data. 
"""

from pathlib import Path
import pandas as pd
import numpy as np

raw_data = Path("data", "raw")
interim_data = Path("data", "interim")


def exp_distribution(series: pd.Series):
    """
    Python implementation of the exponentiation transformation
    from the IMD methodology.

    Takes an input of an index, with 1 being the most deprived
    and returns a scale between 1 and 100 - with more difference being
    indicated between the most deprived areas.

    """

    ln = np.log
    exp = np.exp
    reversed_series = (len(series) - series) + 1
    scaled_rank = reversed_series / len(series)
    transformed_score = -23 * ln(1 - scaled_rank * (1 - exp(-100 / 23)))

    return transformed_score


def create_missing_scores(
    origin: Path,
    destination: Path,
    weight_mapping: dict[str, float],
    reduce_to: list[str],
    rank_var: str,
):
    """
    Create missing overall core and rank from the composite of the different subdomains
    """
    df = pd.read_csv(origin)

    overall = None
    total_weight = 0
    for col, weight in weight_mapping.items():
        total_weight += weight
        current_col = exp_distribution(df[col]) * weight
        if overall is None:
            overall = current_col
        else:
            overall += current_col

    assert total_weight == 1
    df["overall_imd_score"] = overall

    df = df[reduce_to + ["overall_imd_score"]]
    df["new_rank"] = df["overall_imd_score"].rank(ascending=False)
    df["agreement"] = df["new_rank"] == df[rank_var]
    diff = df["new_rank"] - df[rank_var]
    diff = diff[diff != 0]

    rank_disagreement = (len(df) - df["agreement"].sum()) / len(df)
    rank_disagreement = round(rank_disagreement * 100, 1)
    print("Disagreement with {1} - {0}%".format(rank_disagreement, rank_var))
    print("Average disagreement scale {0}".format(diff.abs().mean()))
    df.to_csv(destination, index=False)
    return df


def create_ni2017():
    """
    Create the overall score for the 2017 NI ranking
    """
    origin = Path(raw_data, "country_indexes", "nimdm2017", "nimdm2017-soa.csv")
    destination = Path(
        interim_data, "country_indexes", "nimdm2017", "nimdm2017-soa-withoverall.csv"
    )
    map = {
        "D1_Income_rank": 0.25,
        "D2_Empl_rank": 0.25,
        "D3_Health_rank": 0.15,
        "P4_Education_rank": 0.15,
        "P5_Access_rank": 0.10,
        "D6_LivEnv_rank": 0.05,
        "D7_CD_rank": 0.05,
    }
    reduce_to = ["SOA2001", "MDM_rank", "Income_perc", "Empl_perc"]
    rank_var = "MDM_rank"
    df = create_missing_scores(origin, destination, map, reduce_to, rank_var)
    indicators = pd.read_csv(
        Path(raw_data, "country_indexes", "nimdm2017", "2010-income-indicator.csv")
    )
    df = pd.merge(df, indicators, on="SOA2001")
    df["2010_income_score"] = df["2010_income_score"] * 100
    df.to_csv(destination, index=False)


def create_simd2020():
    """
    Create the overall score for the 2020 Scotland ranking
    """
    origin = Path(raw_data, "country_indexes", "simd2020", "SIMD+2020v2+-+ranks.csv")
    destination = Path(
        interim_data, "country_indexes", "simd2020", "simd2020-with-overall.csv"
    )
    map = {
        "SIMD2020v2_Income_Domain_Rank": 0.28,
        "SIMD2020_Health_Domain_Rank": 0.14,
        "SIMD2020_Access_Domain_Rank": 0.09,
        "SIMD2020_Employment_Domain_Rank": 0.28,
        "SIMD2020_Education_Domain_Rank": 0.14,
        "SIMD2020_Crime_Domain_Rank": 0.05,
        "SIMD2020_Housing_Domain_Rank": 0.02,
    }

    reduce_to = [
        "Data_Zone",
        "SIMD2020v2_Rank",
        "SIMD2020v2_Income_Domain_Rank",
        "SIMD2020_Employment_Domain_Rank",
    ]
    rank_var = "SIMD2020v2_Rank"
    df = create_missing_scores(origin, destination, map, reduce_to, rank_var)

    indicators = pd.read_csv(
        Path(
            "data", "raw", "country_indexes", "simd2020", "SIMD+2020v2+-+indicators.csv"
        )
    )
    indicators = indicators[["Data_Zone", "Income_rate", "Employment_rate"]]
    df = pd.merge(df, indicators, on="Data_Zone")

    df.to_csv(destination, index=False)


def create_wimd2019():
    """
    Create the overall score for the 2019 Wales ranking
    """
    origin = Path(
        raw_data, "country_indexes", "wimd2019", "wimd-2019-index-and-domain-scores.csv"
    )
    destination = Path(
        interim_data,
        "country_indexes",
        "wimd2019",
        "wimd-2019-index-and-domain-scores-overall.csv",
    )

    df = pd.read_csv(origin)
    indicators = pd.read_csv(
        Path(raw_data, "country_indexes", "wimd2019", "indicators.csv")
    )
    indicators = indicators[["lsoa", "indicator_income", "indicator_employment"]]
    df = pd.merge(df, indicators, on="lsoa")
    df.to_csv(destination, index=False)


def fill_in_scores():
    """
    Fill in missing data for non-English indexes
    """
    create_ni2017()
    create_simd2020()
    create_wimd2019()


if __name__ == "__main__":
    fill_in_scores()
