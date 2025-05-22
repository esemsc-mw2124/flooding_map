import pandas as pd

df = pd.read_excel("comprehensive_slr_projections.xlsx")

avg_slr = df.groupby(['Scenario', 'Year'])['Projected_SLR_m'].mean().reset_index()

avg_slr['Projected_SLR_m'] = avg_slr['Projected_SLR_m'].round(1)


def get_scenario(scenario):
    if scenario == "SSP1-1.9":
        return avg_slr.loc[avg_slr['Scenario'] == "ssp119"].drop(columns=['Scenario'])
    elif scenario == "SSP2-4.5":
        return avg_slr.loc[avg_slr['Scenario'] == "ssp245"].drop(columns=['Scenario'])
    elif scenario == "SSP5-8.5":
        return avg_slr.loc[avg_slr['Scenario'] == "ssp245"].drop(columns=['Scenario'])
    else:
        raise ValueError("Invalid scenario")