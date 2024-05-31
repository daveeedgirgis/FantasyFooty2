import streamlit as st
import requests
import pandas as pd
import altair as alt

# Set up the Streamlit app
st.title("Premier League Fantasy Football Dashboard")
st.write("Welcome to the Premier League Fantasy Football Dashboard!")

# Input for League ID
league_id = st.text_input("Enter your League ID:", value="148968")

# Fetch data from the API
@st.cache_data
def fetch_data(league_id):
    url = f"https://draft.premierleague.com/api/league/{league_id}/details"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data. Please check the League ID.")
        return None

data = fetch_data(league_id)

if data:
    # Process the data
    league_name = data['league']['name']
    league_entries = data['league_entries']
    standings = data['standings']

    st.subheader(f"League: {league_name}")

    # Convert to DataFrame
    league_entries_df = pd.DataFrame(league_entries)
    standings_df = pd.DataFrame(standings)

    # Display raw data for debugging
    st.write("## Raw League Entries Data")
    st.write(league_entries_df)
    st.write("## Raw Standings Data")
    st.write(standings_df)

    # Ensure the merge keys are of the same type
    standings_df['league_entry'] = standings_df['league_entry'].astype(str)
    league_entries_df['id'] = league_entries_df['id'].astype(str)

    # Identify mismatched IDs
    standings_ids = set(standings_df['league_entry'].unique())
    entries_ids = set(league_entries_df['id'].unique())

    missing_in_entries = standings_ids - entries_ids
    missing_in_standings = entries_ids - standings_ids

    if missing_in_entries:
        st.warning(f"IDs in standings but not in league entries: {missing_in_entries}")
    if missing_in_standings:
        st.warning(f"IDs in league entries but not in standings: {missing_in_standings}")

    # Filter valid entries for merging
    valid_standings_df = standings_df[standings_df['league_entry'].isin(entries_ids)]
    valid_entries_df = league_entries_df[league_entries_df['id'].isin(standings_ids)]

    # Check if valid data is available after filtering
    if valid_standings_df.empty:
        st.error("No valid standings data available after filtering.")
    if valid_entries_df.empty:
        st.error("No valid league entries data available after filtering.")

    # Merge the valid data
    if not valid_standings_df.empty and not valid_entries_df.empty:
        merged_df = valid_standings_df.merge(
            valid_entries_df[['id', 'entry_name', 'joined_time', 'player_first_name', 'player_last_name']],
            left_on='league_entry', right_on='id', how='left'
        )

        if merged_df.empty:
            st.error("Merged Data is empty after attempting to merge valid entries and standings.")
        else:
            # Display merged data for debugging
            st.write("## Merged Data")
            st.write(merged_df)

            # Ensure 'total' is numeric and handle missing values
            merged_df['total'] = pd.to_numeric(merged_df['total'], errors='coerce').fillna(0)

            # Display standings in a table
            st.write("## League Standings")
            st.dataframe(merged_df[['entry_name', 'player_first_name', 'player_last_name', 'total']])

            # Total Points Distribution
            st.write("## Total Points Distribution")
            chart = alt.Chart(merged_df).mark_bar().encode(
                x=alt.X('entry_name', sort='-y', title='Team Name'),
                y=alt.Y('total', title='Total Points'),
                tooltip=['entry_name', 'total']
            ).properties(
                width=700,
                height=400,
                title="Total Points Distribution"
            )
            st.altair_chart(chart)

            # Points Distribution Histogram
            st.write("## Points Distribution Histogram")
            histogram = alt.Chart(merged_df).mark_bar().encode(
                x=alt.X('total', bin=True, title='Total Points'),
                y=alt.Y('count()', title='Count of Teams'),
                tooltip=['count()']
            ).properties(
                width=700,
                height=400,
                title="Histogram of Total Points"
            )
            st.altair_chart(histogram)

            # Top Scorers
            st.write("## Top 10 Scoring Teams")
            top_scorers = alt.Chart(merged_df.nlargest(10, 'total')).mark_bar().encode(
                x=alt.X('entry_name', sort='-y', title='Team Name'),
                y=alt.Y('total', title='Total Points'),
                color='entry_name',
                tooltip=['entry_name', 'total']
            ).properties(
                width=700,
                height=400,
                title="Top 10 Scoring Teams"
            )
            st.altair_chart(top_scorers)

            # Win-Loss Record
            st.write("## Win-Loss Record")
            wins_chart = alt.Chart(merged_df).mark_bar(color='green').encode(
                x=alt.X('entry_name', sort='-y', title='Team Name'),
                y=alt.Y('matches_won', title='Wins'),
                tooltip=['entry_name', 'matches_won']
            ).properties(
                width=700,
                height=400,
                title="Wins"
            )

            losses_chart = alt.Chart(merged_df).mark_bar(color='red').encode(
                x=alt.X('entry_name', sort='-y', title='Team Name'),
                y=alt.Y('matches_lost', title='Losses'),
                tooltip=['entry_name', 'matches_lost']
            ).properties(
                width=700,
                height=400,
                title="Losses"
            )

            draws_chart = alt.Chart(merged_df).mark_bar(color='blue').encode(
                x=alt.X('entry_name', sort='-y', title='Team Name'),
                y=alt.Y('matches_drawn', title='Draws'),
                tooltip=['entry_name', 'matches_drawn']
            ).properties(
                width=700,
                height=400,
                title="Draws"
            )

            st.altair_chart(wins_chart)
            st.altair_chart(losses_chart)
            st.altair_chart(draws_chart)

            # Highlight the top scorer
            if not merged_df.empty and merged_df['total'].max() > 0:
                top_scorer = merged_df.loc[merged_df['total'].idxmax()]
                st.write("## Points Leader")
                st.metric(label="Top Scorer", value=top_scorer['total'])
                st.write(f"Player: {top_scorer['player_first_name']} {top_scorer['player_last_name']}")
            else:
                st.write("No valid data available to determine the top scorer.")
else:
    st.write("Enter a valid League ID to see the standings.")
