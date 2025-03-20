#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   server.py
@Time    :   2024/02/20
@Author  :   Taylor Firman
@Version :   1.0
@Contact :   tefirman@gmail.com
@Desc    :   Server logic for March Madness bracket app
'''

from shiny import render, ui, reactive
from shiny.types import SilentException
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path
from markdown import markdown
from bigdance.cbb_brackets import Bracket, Team

from data import teams

logger = logging.getLogger(__name__)

# Analysis data containers - will be populated reactively based on pool size
optimal_upset_df = None
champion_df = None
specific_upsets_df = None
analysis_summary = None
upset_stats_df = None
log_prob_df = None
optimal_upset_dict = None

# Default optimal values if files not found
default_optimal_upset_dict = {
    "First Round": {"optimal": 10, "range": (8, 11)},
    "Second Round": {"optimal": 7, "range": (6, 8)},
    "Sweet 16": {"optimal": 2, "range": (2, 4)},
    "Elite 8": {"optimal": 1, "range": (1, 3)},
    "Final Four": {"optimal": 1, "range": (0, 1)},
    "Championship": {"optimal": 0, "range": (0, 1)},
    "Total": {"optimal": 18, "range": (18, 25)}
}

def load_analysis_data(pool_size: str) -> Dict:
    """Load analysis data based on pool size"""
    global optimal_upset_df, champion_df, specific_upsets_df, analysis_summary
    global upset_stats_df, log_prob_df, optimal_upset_dict
    
    try:
        # Determine the directory path based on pool size
        analysis_dir = Path(f'analysis_data/men_{pool_size}entries')
        
        # Check if analysis data directory exists
        if not analysis_dir.exists():
            analysis_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Analysis data directory for {pool_size} entries created. Please add analysis files.")
        
        # Load optimal upset strategy
        optimal_upset_path = analysis_dir / 'optimal_upset_strategy.csv'
        if optimal_upset_path.exists():
            optimal_upset_df = pd.read_csv(optimal_upset_path)
        else:
            logger.warning(f"Optimal upset strategy file not found for {pool_size} entries")
            optimal_upset_df = None
        
        # Load champion pick comparison data
        champion_path = analysis_dir / 'champion_pick_comparison.csv'
        if champion_path.exists():
            champion_df = pd.read_csv(champion_path)
        else:
            logger.warning(f"Champion pick comparison file not found for {pool_size} entries")
            champion_df = None
        
        # Load specific upsets data
        specific_upsets_path = analysis_dir / 'specific_upset_comparison.csv'
        if specific_upsets_path.exists():
            specific_upsets_df = pd.read_csv(specific_upsets_path)
        else:
            logger.warning(f"Specific upsets file not found for {pool_size} entries")
            specific_upsets_df = None
        
        # Load historical data summary
        summary_path = analysis_dir / 'comparative_analysis_summary.md'
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                analysis_summary = f.read()
        else:
            logger.warning(f"Comparative analysis summary file not found for {pool_size} entries")
            analysis_summary = None
            
        # Load upset comparison statistics
        upset_stats_path = analysis_dir / 'upset_comparison_statistics.csv'
        if upset_stats_path.exists():
            upset_stats_df = pd.read_csv(upset_stats_path)
        else:
            logger.warning(f"Upset comparison statistics file not found for {pool_size} entries")
            upset_stats_df = None
        
        # Load log probability comparison statistics
        log_prob_path = analysis_dir / 'log_probability_comparison_statistics.csv'
        if log_prob_path.exists():
            log_prob_df = pd.read_csv(log_prob_path)
        else:
            logger.warning(f"Log probability comparison statistics file not found for {pool_size} entries")
            log_prob_df = None
        
        # Create optimal upset dictionary
        if optimal_upset_df is not None:
            optimal_upset_dict = {row['round']: {"optimal": int(row['max_advantage_upsets']), 
                                                "range": (max(0, int(row['max_advantage_upsets'] - 2)), 
                                                         int(row['max_advantage_upsets'] + 2))}
                                 for _, row in optimal_upset_df.iterrows() if row['round'] != 'Total Upsets'}
            # Add total upsets
            total_row = optimal_upset_df[optimal_upset_df['round'] == 'Total Upsets']
            if not total_row.empty:
                optimal_upset_dict["Total"] = {"optimal": int(total_row['max_advantage_upsets'].iloc[0]),
                                              "range": (int(total_row['max_advantage_upsets'].iloc[0] - 4),
                                                        int(total_row['max_advantage_upsets'].iloc[0] + 4))}
            else:
                optimal_upset_dict["Total"] = {"optimal": 22, "range": (18, 26)}
        else:
            optimal_upset_dict = default_optimal_upset_dict

        return {
            'success': True,
            'message': f"Loaded analysis data for {pool_size} entries"
        }
    except Exception as e:
        logger.error(f"Error loading analysis data for {pool_size} entries: {str(e)}")
        optimal_upset_dict = default_optimal_upset_dict
        return {
            'success': False,
            'message': f"Error loading analysis data: {str(e)}",
            'error': str(e)
        }

def get_game_winner(input, game_id: str) -> Optional[str]:
    """Helper function to safely get game winner"""
    try:
        return input[game_id]()
    except SilentException:
        return None
    except Exception as e:
        logger.error(f"Error getting winner for {game_id}: {str(e)}")
        return None

def get_bracket(input) -> 'Bracket':
    """
    Get or create the current bracket based on UI selections.
    This function can be called from anywhere to get the current state of the bracket.
    
    Args:
        input: Shiny input object containing user selections
        
    Returns:
        Bracket object representing the current state of the bracket
    """
    # Use a reactive value cache if we implement this in Shiny
    return create_bracket_from_picks(input)

def convert_team_to_dict(team: 'Team') -> Dict:
    """
    Convert a Team object to a dictionary format compatible with the UI.
    
    Args:
        team: Team object from the Bracket class
        
    Returns:
        Dictionary representation of the team
    """
    if team is None:
        return None
        
    return {
        "Team": team.name,
        "Seed": team.seed,
        "Rating": team.rating,
        "Conference": team.conference,
        "Region": team.region
    }

def get_matchups_for_round(input, region: str, round_num: int) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    """
    Get matchups for a specific region and round based on the current bracket state.
    
    Args:
        input: Shiny input object containing user selections
        region: Region name (East, West, South, Midwest)
        round_num: Round number (1-4)
        
    Returns:
        List of tuple pairs (team1, team2) representing matchups, in dict format for UI
    """
    from bigdance.cbb_brackets import Game
    
    # Create or get the bracket
    bracket = get_bracket(input)
    
    # For first round, the games are already defined in the bracket
    if round_num == 1:
        # Filter games from the first round in this region
        matchups = []
        for game in bracket.games:
            if game.region.lower() == region.lower():
                matchups.append((
                    convert_team_to_dict(game.team1),
                    convert_team_to_dict(game.team2)
                ))
        return matchups
    
    # For later rounds, we need to construct the games based on winners from previous rounds
    # Map round_num to round names used in bracket.results
    round_names = {
        1: "First Round",
        2: "Second Round",
        3: "Sweet 16",
        4: "Elite 8",
        5: "Final Four",
        6: "Championship"
    }
    
    # Get winners from the previous round
    prev_round_name = round_names[round_num - 1]
    if prev_round_name not in bracket.results:
        # No results for previous round yet
        return [(None, None)] * (2**(4 - round_num))  # Return empty matchups
    
    # Filter teams from the previous round in this region
    region_teams = [team for team in bracket.results[prev_round_name] 
                   if team.region.lower() == region.lower()]
    
    # Create matchups for the current round
    matchups = []
    for i in range(0, len(region_teams), 2):
        team1 = region_teams[i] if i < len(region_teams) else None
        team2 = region_teams[i+1] if i+1 < len(region_teams) else None
        matchups.append((
            convert_team_to_dict(team1),
            convert_team_to_dict(team2)
        ))
    
    return matchups

def get_final_four_matchups(input) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    """Get Final Four matchups based on Elite 8 winners"""
    bracket = get_bracket(input)
    
    # Check if Elite 8 results exist
    if "Elite 8" not in bracket.results:
        return [(None, None), (None, None)]
    
    # Get regional champions
    elite_eight_winners = bracket.results["Elite 8"]
    
    # Create Final Four matchups (traditionally East vs West, South vs Midwest)
    region_to_index = {"East": 0, "West": 1, "South": 2, "Midwest": 3}
    
    # Sort winners by region to ensure consistent matchups
    sorted_winners = sorted(elite_eight_winners, key=lambda team: region_to_index.get(team.region, 99))
    
    # Create matchups
    matchups = []
    for i in range(0, len(sorted_winners), 2):
        team1 = sorted_winners[i] if i < len(sorted_winners) else None
        team2 = sorted_winners[i+1] if i+1 < len(sorted_winners) else None
        matchups.append((
            convert_team_to_dict(team1),
            convert_team_to_dict(team2)
        ))
    
    # Ensure we return exactly 2 matchups
    while len(matchups) < 2:
        matchups.append((None, None))
    
    return matchups

def get_championship_matchup(input) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    """Get Championship matchup based on Final Four winners"""
    bracket = get_bracket(input)
    
    # Check if Final Four results exist
    if "Final Four" not in bracket.results or not bracket.results["Final Four"]:
        return [(None, None)]
    
    final_four_winners = bracket.results["Final Four"]
    
    # Create Championship matchup
    if len(final_four_winners) >= 2:
        return [(
            convert_team_to_dict(final_four_winners[0]),
            convert_team_to_dict(final_four_winners[1])
        )]
    else:
        return [(None, None)]

# Replace the specific functions with a general function that calls the shared implementation
def get_round1_matchups(region: str) -> List[Tuple[Optional[Dict], Optional[Dict]]]:
    """Get initial matchups for first round games in a region"""
    # Create bracket using initial teams data
    from bigdance.cbb_brackets import Bracket, Team
    
    all_teams = []
    for region_name, region_teams in teams.items():
        for team_data in region_teams:
            all_teams.append(Team(
                name=team_data["Team"],
                seed=team_data["Seed"],
                region=region_name,
                rating=team_data.get("Rating", 1500),
                conference="Unknown"
            ))
    
    bracket = Bracket(all_teams)
    
    # Filter games in specified region
    matchups = []
    for game in bracket.games:
        if game.region.lower() == region.lower():
            matchups.append((
                convert_team_to_dict(game.team1),
                convert_team_to_dict(game.team2)
            ))
    
    return matchups

def create_round_ui(input, region: str, round_num: int, matchups: List[Tuple[Dict, Dict]]) -> ui.div:
    """
    Create UI for any round's games with higher seed selected by default,
    while preserving user selections when possible.
    """
    games = []
    for i, (team1, team2) in enumerate(matchups):
        game_id = f"{region.lower()}_round{round_num}_game_{i}"
        choices = {}
        
        if team1:
            choices[team1["Team"]] = f"({team1['Seed']}) {team1['Team']}"
        if team2:
            choices[team2["Team"]] = f"({team2['Seed']}) {team2['Team']}"
        
        if len(choices) == 2:
            # Try to get current selection (if any)
            current_selection = None
            try:
                current_selection = input[game_id]()
            except:
                # No selection yet or other error
                pass
                
            # If current selection exists and is still valid, keep it
            if current_selection and current_selection in choices:
                default_team = current_selection
            else:
                # Otherwise default to higher seed
                default_team = team1["Team"] if team1["Seed"] < team2["Seed"] else team2["Team"]
            
            game = ui.div(
                {"class": "game-container"},
                ui.input_radio_buttons(
                    game_id,
                    f"Game {i + 1}",
                    choices,
                    selected=default_team
                )
            )
        else:
            game = ui.div(
                {"class": "game-container"},
                ui.p("Waiting for previous round selections...")
            )
        
        games.append(game)
    
    return ui.div(
        {"class": "bracket-region"},
        *games
    )

def create_bracket_from_picks(input) -> Bracket:
    """
    Create a Bracket object from the user's selections in the UI.
    
    Args:
        input: Shiny input object containing user selections
        
    Returns:
        Bracket object populated with the user's picks
    """
    # Create Team objects from teams data
    all_teams = []
    for region_name, region_teams in teams.items():
        for team_data in region_teams:
            all_teams.append(Team(
                name=team_data["Team"],
                seed=team_data["Seed"],
                region=region_name,
                rating=team_data.get("Rating", 1500),
                conference="Unknown"  # Conference not critical for analysis
            ))
    
    # Create an empty bracket with these teams
    bracket = Bracket(all_teams)
    
    # Initialize results dictionary
    bracket.results = {
        "First Round": [],
        "Second Round": [],
        "Sweet 16": [],
        "Elite 8": [],
        "Final Four": [],
        "Championship": []
    }
    
    # Get user selections for each round
    # First round through Elite 8 (regions)
    for region in ["east", "west", "south", "midwest"]:
        # First round (8 games)
        for i in range(8):
            game_id = f"{region}_round1_game_{i}"
            winner_name = get_game_winner(input, game_id)
            if winner_name:
                winner = next((t for t in all_teams if t.name == winner_name), None)
                if winner:
                    bracket.results["First Round"].append(winner)
        
        # Second round (4 games)
        for i in range(4):
            game_id = f"{region}_round2_game_{i}"
            winner_name = get_game_winner(input, game_id)
            if winner_name:
                winner = next((t for t in all_teams if t.name == winner_name), None)
                if winner:
                    bracket.results["Second Round"].append(winner)
        
        # Sweet 16 (2 games)
        for i in range(2):
            game_id = f"{region}_round3_game_{i}"
            winner_name = get_game_winner(input, game_id)
            if winner_name:
                winner = next((t for t in all_teams if t.name == winner_name), None)
                if winner:
                    bracket.results["Sweet 16"].append(winner)
        
        # Elite 8 (1 game)
        game_id = f"{region}_round4_game_0"
        winner_name = get_game_winner(input, game_id)
        if winner_name:
            winner = next((t for t in all_teams if t.name == winner_name), None)
            if winner:
                bracket.results["Elite 8"].append(winner)
    
    # Final Four (2 games)
    for i in range(2):
        game_id = f"final_round5_game_{i}"
        winner_name = get_game_winner(input, game_id)
        if winner_name:
            winner = next((t for t in all_teams if t.name == winner_name), None)
            if winner:
                bracket.results["Final Four"].append(winner)
    
    # Championship (1 game)
    game_id = "final_round6_game_0"
    winner_name = get_game_winner(input, game_id)
    if winner_name:
        winner = next((t for t in all_teams if t.name == winner_name), None)
        if winner:
            bracket.results["Championship"].append(winner)
            bracket.results["Champion"] = winner
    
    return bracket


def analyze_bracket(input) -> Dict:
    """
    Analyze the current bracket selections and provide recommendations
    """
    try:
        # Create a Bracket object from user selections
        bracket = create_bracket_from_picks(input)
        
        # Extract simple selection dictionary for compatibility with other functions
        # (in case any of them still need access to the selections)
        selections = {
            round_name: [team.name for team in teams_list] 
            for round_name, teams_list in bracket.results.items() 
            if round_name != "Champion"
        }
        
        # Add Champion separately since it's a single Team object
        if "Champion" in bracket.results and bracket.results["Champion"]:
            selections["Champion"] = bracket.results["Champion"].name
        else:
            selections["Champion"] = None
        
        # Use Bracket built-in methods for underdogs analysis
        bracket.identify_underdogs()
        underdog_counts = bracket.count_underdogs_by_round()
        underdog_counts["Total"] = bracket.total_underdogs()
        
        # Get specific upsets
        specific_upsets = []
        if specific_upsets_df is not None:
            for round_name, team_list in bracket.underdogs_by_round.items():
                for team in team_list:
                    # Check if this is an upset according to the analysis
                    round_upsets = specific_upsets_df[
                        (specific_upsets_df['round'] == round_name) & 
                        (specific_upsets_df['team'] == team.name) &
                        (specific_upsets_df['seed'] == team.seed)
                    ]
                    
                    if not round_upsets.empty and round_upsets['freq_diff'].values[0] > 0:
                        # This is a valuable upset - add it to our list
                        upset_value = round_upsets['freq_diff'].values[0]
                        specific_upsets.append({
                            'round': round_name,
                            'team': team.name,
                            'seed': team.seed,
                            'region': team.region,
                            'advantage': upset_value
                        })
        
        # Evaluate champion selection
        champion_assessment = {
            'champion': selections["Champion"],
            'value': 0,
            'recommendation': None
        }
        
        if champion_df is not None and selections["Champion"]:
            champion_row = champion_df[champion_df['team'] == selections["Champion"]]
            if not champion_row.empty:
                champion_assessment['value'] = champion_row['freq_diff'].values[0]
                
                if champion_assessment['value'] < 0:
                    # Get top 3 recommended champions
                    top_champions = champion_df[champion_df['freq_diff'] > 0].sort_values('freq_diff', ascending=False).head(3)
                    if not top_champions.empty:
                        # Add region information to recommendations
                        champion_recommendations = []
                        for _, champ in top_champions.iterrows():
                            champ_name = champ['team']
                            champ_region = None
                            
                            # Find region
                            for region, region_teams in teams.items():
                                if any(team["Team"] == champ_name for team in region_teams):
                                    champ_region = region
                                    break
                                    
                            champion_recommendations.append({
                                'team': champ_name,
                                'seed': champ['seed'],
                                'region': champ_region,
                                'freq_diff': champ['freq_diff']
                            })
                            
                        champion_assessment['recommendation'] = champion_recommendations
            else:
                # Champion not found in analysis, recommend top 3
                top_champions = champion_df[champion_df['freq_diff'] > 0].sort_values('freq_diff', ascending=False).head(3)
                if not top_champions.empty:
                    # Add region information to recommendations
                    champion_recommendations = []
                    for _, champ in top_champions.iterrows():
                        champ_name = champ['team']
                        champ_region = None
                        
                        # Find region
                        for region, region_teams in teams.items():
                            if any(team["Team"] == champ_name for team in region_teams):
                                champ_region = region
                                break
                                
                        champion_recommendations.append({
                            'team': champ_name,
                            'seed': champ['seed'],
                            'region': champ_region,
                            'freq_diff': champ['freq_diff']
                        })
                        
                    champion_assessment['recommendation'] = champion_recommendations
        
        # Compare underdog counts to optimal values
        upset_assessment = {}
        for round_name, count in underdog_counts.items():
            if round_name in optimal_upset_dict:
                optimal = optimal_upset_dict[round_name]["optimal"]
                optimal_range = optimal_upset_dict[round_name]["range"]
                
                upset_assessment[round_name] = {
                    'count': count,
                    'optimal': optimal,
                    'min': optimal_range[0],
                    'max': optimal_range[1],
                    'status': 'good' if optimal_range[0] <= count <= optimal_range[1] else 
                              ('too_many' if count > optimal_range[1] else 'too_few')
                }
        
        # Find valuable upsets that user is missing
        missing_valuable_upsets = []
        if specific_upsets_df is not None:
            # Get top 10 most valuable specific upsets
            top_upsets = specific_upsets_df[specific_upsets_df['freq_diff'] > 0].sort_values('freq_diff', ascending=False).head(10)
            
            for _, upset in top_upsets.iterrows():
                round_name = upset['round']
                team_name = upset['team']
                
                # Check if this valuable upset is missing from user's selections
                is_missing = True
                if round_name in selections:
                    if team_name in selections[round_name]:
                        is_missing = False
                
                if is_missing:
                    # Find team region
                    team_region = None
                    for region, region_teams in teams.items():
                        if any(team["Team"] == team_name for team in region_teams):
                            team_region = region
                            break
                            
                    missing_valuable_upsets.append({
                        'round': round_name,
                        'team': team_name,
                        'seed': upset['seed'],
                        'region': team_region,
                        'advantage': upset['freq_diff']
                    })
        
        # Overall assessment
        bracket_score = 0
        
        # Add points for having optimal number of upsets
        for round_name, assessment in upset_assessment.items():
            if assessment['status'] == 'good':
                bracket_score += 5
            elif assessment['status'] == 'too_many' and assessment['count'] - assessment['max'] <= 2:
                bracket_score += 2
            elif assessment['status'] == 'too_few' and assessment['min'] - assessment['count'] <= 2:
                bracket_score += 2
        
        # Add points for valuable specific upsets
        bracket_score += len(specific_upsets) * 3
        
        # Add points for champion selection
        if champion_assessment['value'] > 0:
            bracket_score += 10
        
        # Maximum possible score: 
        # 7 rounds * 5 points + 10 valuable upsets * 3 points + champion 10 points = 75
        bracket_rating = {
            'score': bracket_score,
            'max_score': 75,
            'percentage': int(bracket_score / 75 * 100),
            'rating': 'Excellent' if bracket_score >= 60 else
                     'Very Good' if bracket_score >= 45 else
                     'Good' if bracket_score >= 30 else
                     'Fair' if bracket_score >= 15 else
                     'Needs Improvement'
        }
        
        return {
            'selections': selections,
            'underdog_counts': underdog_counts,
            'specific_upsets': specific_upsets,
            'missing_valuable_upsets': missing_valuable_upsets,
            'champion_assessment': champion_assessment,
            'upset_assessment': upset_assessment,
            'bracket_rating': bracket_rating
        }
    
    except Exception as e:
        logger.error(f"Error analyzing bracket: {str(e)}")
        return {
            'error': str(e),
            'selections': {},
            'underdog_counts': {},
            'specific_upsets': [],
            'missing_valuable_upsets': [],
            'champion_assessment': {},
            'upset_assessment': {},
            'bracket_rating': {'rating': 'Error', 'score': 0, 'max_score': 75, 'percentage': 0}
        }

def format_bracket_assessment(assessment: Dict, input) -> str:
    """Format bracket assessment into a readable text report"""
    try:
        if 'error' in assessment:
            return f"Error analyzing bracket: {assessment['error']}"
        
        # Get pool size for context
        pool_size = input.pool_size()
        
        # General format
        report = [
            f"# Bracket Assessment for {pool_size}-Entry Pool",
            f"## Overall Rating: {assessment['bracket_rating']['rating']} ({assessment['bracket_rating']['score']}/{assessment['bracket_rating']['max_score']} points)"
        ]
        
        # Upset assessment
        report.append("## Upset Analysis")
        expected_rounds = ["First Round", "Second Round", "Sweet 16", "Elite 8", "Final Four", "Championship", "Total"]
        for round_name in expected_rounds:
            if round_name in assessment['upset_assessment']:
                details = assessment['upset_assessment'][round_name]
                status_emoji = "✅" if details['status'] == 'good' else "⚠️" if details['status'] == 'too_many' else "❗"
                report_line = f"{status_emoji} **{round_name}**: {details['count']} upsets "
                
                if details['status'] == 'good':
                    report_line += f"(optimal range is {details['min']}-{details['max']})"
                elif details['status'] == 'too_many':
                    report_line += f"(consider reducing by {details['count'] - details['max']} to reach optimal range of {details['min']}-{details['max']})"
                else:  # too_few
                    report_line += f"(consider adding {details['min'] - details['count']} to reach optimal range of {details['min']}-{details['max']})"
                
                report.append(report_line)
            else:
                # Skip or add placeholder for missing rounds
                if round_name != "Total":  # Don't show message for Total if missing
                    report.append(f"⚠️ **{round_name}**: No data available")
        
        # Champion assessment
        report.append("## Champion Selection")
        if assessment['champion_assessment']['champion']:
            # Find champion details
            champion_name = assessment['champion_assessment']['champion']
            champion_details = next((team for region_teams in teams.values() 
                                 for team in region_teams if team["Team"] == champion_name), None)
            if champion_details:
                champion_seed = champion_details['Seed']
                
                # Find champion region
                champion_region = None
                for region, region_teams in teams.items():
                    if any(team["Team"] == champion_name for team in region_teams):
                        champion_region = region
                        break
                        
                region_info = f" [{champion_region}]" if champion_region else ""
                report.append(f"Your champion: **({champion_seed}) {champion_name}{region_info}**")
                
                if assessment['champion_assessment']['value'] > 0:
                    report.append(f"✅ Good choice! This champion appears more frequently in winning brackets.")
                elif assessment['champion_assessment']['value'] == 0:
                    report.append(f"⚠️ Neutral choice. This champion appears equally in winning and non-winning brackets.")
                else:
                    report.append(f"❗ Consider a different champion. This pick appears more frequently in non-winning brackets.")
                    
                    if assessment['champion_assessment']['recommendation']:
                        report.append("Suggested champion alternatives:")
                        for idx, champ in enumerate(assessment['champion_assessment']['recommendation']):
                            region_info = f" [{champ.get('region', '')}]" if 'region' in champ else ""
                            report.append(f"- ({champ['seed']}) {champ['team']}{region_info}")
            else:
                report.append(f"Your champion: **{champion_name}**")
        else:
            report.append("❗ No champion selected. Please complete your bracket.")
        
        # Valuable specific upsets
        report.append("## Valuable Upsets")
        if assessment['specific_upsets']:
            report.append(f"✅ Your bracket includes these valuable upset picks that appear more often in winning brackets in {pool_size}-entry pools:")
            for upset in sorted(assessment['specific_upsets'], key=lambda x: x['advantage'], reverse=True):
                # Include region information
                region_info = f" [{upset.get('region', '')}]" if 'region' in upset else ""
                report.append(f"- **{upset['round']}**: ({upset['seed']}) {upset['team']}{region_info}")
        else:
            report.append("⚠️ Your bracket doesn't include any of the specific upsets that frequently appear in winning brackets.")
        
        if assessment['missing_valuable_upsets']:
            report.append(f"### Consider adding these valuable upsets for {pool_size}-entry pools:")
            for upset in assessment['missing_valuable_upsets'][:5]:  # Top 5 recommendations
                # Include region information
                region_info = f" [{upset.get('region', '')}]" if 'region' in upset else ""
                report.append(f"- **{upset['round']}**: ({upset['seed']}) {upset['team']}{region_info}")
                
        # General advice
        report.append("## General Advice")
        
        # Add round-specific advice based on analysis
        advice_points = []
        
        if "First Round" in assessment['upset_assessment']:
            if assessment['upset_assessment']['First Round']['status'] == 'too_many':
                advice_points.append("- **First Round**: You've selected too many upsets. Historically, winning brackets have fewer first-round upsets than you might expect.")
            elif assessment['upset_assessment']['First Round']['status'] == 'too_few':
                advice_points.append("- **First Round**: Consider adding a few more first-round upsets, particularly in the 10-12 seed range.")
        if "Second Round" in assessment['upset_assessment']:
            if assessment['upset_assessment']['Second Round']['status'] == 'too_many':
                advice_points.append("- **Second Round**: You may have too many second-round upsets. Consider keeping more 1-4 seeds advancing to the Sweet 16.")
        
        if "Sweet 16" in assessment['upset_assessment'] and "Elite 8" in assessment['upset_assessment']:
            # Add Sweet 16/Elite 8 advice based on pattern
            sweet16_count = assessment['upset_assessment']['Sweet 16']['count']
            elite8_count = assessment['upset_assessment']['Elite 8']['count']
            
            if sweet16_count > 4 and elite8_count > 2:
                advice_points.append("- **Later Rounds**: Your bracket has many upsets in the later rounds. While exciting, this reduces your likelihood of success.")
        
        # Final Four advice
        final_four_picks = assessment['selections'].get('Final Four', [])
        final_four_seeds = []
        for team in final_four_picks:
            team_details = next((t for region_teams in teams.values() for t in region_teams if t["Team"] == team), None)
            if team_details:
                final_four_seeds.append(team_details['Seed'])
        
        if final_four_seeds and max(final_four_seeds) > 8:
            advice_points.append("- **Final Four**: Your Final Four includes very high seeds. Historically, at least 2-3 of the Final Four teams are 1-4 seeds.")
        
        # Add pool size specific advice
        pool_size_int = int(input.pool_size())
        if pool_size_int <= 10:
            advice_points.append("- **Small Pool Strategy**: In small pools (10 entries or fewer), consider selecting more high seeds since you need fewer surprises to differentiate your bracket.")
        elif pool_size_int >= 500:
            advice_points.append("- **Large Pool Strategy**: In very large pools (500+ entries), you may need more strategic upsets and a less common champion pick to stand out.")
        
        # Add all advice points
        report.extend(advice_points)
            
        # Join with single newlines for proper Markdown rendering
        return "\n".join(report)
    except Exception as e:
        logger.error(f"Error formatting bracket assessment: {str(e)}")
        return f"Error formatting bracket assessment: {str(e)}"

def server(input, output, session):
    """Main server function containing all callbacks and reactive logic"""
    
    # Add reactive effect to update analysis data when pool size changes
    @reactive.Effect
    def _update_analysis_data():
        # Load analysis data based on selected pool size
        pool_size = input.pool_size()
        logger.info(f"Updating analysis data for {pool_size} entries pool")
        load_analysis_data(pool_size)
    
    # Initialize with default pool size on startup
    @reactive.Effect(priority=10)  # Higher priority to run first
    def _init_data():
        # Initial load with default pool size
        load_analysis_data("100")  # Default size
    
    # First Round UI Outputs
    @output
    @render.ui
    def east_bracket_round1():
        return create_round_ui(input, "East", 1, get_round1_matchups("East"))

    @output
    @render.ui
    def west_bracket_round1():
        return create_round_ui(input, "West", 1, get_round1_matchups("West"))

    @output
    @render.ui
    def south_bracket_round1():
        return create_round_ui(input, "South", 1, get_round1_matchups("South"))

    @output
    @render.ui
    def midwest_bracket_round1():
        return create_round_ui(input, "Midwest", 1, get_round1_matchups("Midwest"))

    # Second Round UI Outputs
    @output
    @render.ui
    def east_bracket_round2():
        return create_round_ui(input, "East", 2, get_matchups_for_round(input, "East", 2))

    @output
    @render.ui
    def west_bracket_round2():
        return create_round_ui(input, "West", 2, get_matchups_for_round(input, "West", 2))

    @output
    @render.ui
    def south_bracket_round2():
        return create_round_ui(input, "South", 2, get_matchups_for_round(input, "South", 2))

    @output
    @render.ui
    def midwest_bracket_round2():
        return create_round_ui(input, "Midwest", 2, get_matchups_for_round(input, "Midwest", 2))

    # Third Round UI Outputs
    @output
    @render.ui
    def east_bracket_round3():
        return create_round_ui(input, "East", 3, get_matchups_for_round(input, "East", 3))

    @output
    @render.ui
    def west_bracket_round3():
        return create_round_ui(input, "West", 3, get_matchups_for_round(input, "West", 3))

    @output
    @render.ui
    def south_bracket_round3():
        return create_round_ui(input, "South", 3, get_matchups_for_round(input, "South", 3))

    @output
    @render.ui
    def midwest_bracket_round3():
        return create_round_ui(input, "Midwest", 3, get_matchups_for_round(input, "Midwest", 3))

    # Fourth Round UI Outputs
    @output
    @render.ui
    def east_bracket_round4():
        return create_round_ui(input, "East", 4, get_matchups_for_round(input, "East", 4))

    @output
    @render.ui
    def west_bracket_round4():
        return create_round_ui(input, "West", 4, get_matchups_for_round(input, "West", 4))

    @output
    @render.ui
    def south_bracket_round4():
        return create_round_ui(input, "South", 4, get_matchups_for_round(input, "South", 4))

    @output
    @render.ui
    def midwest_bracket_round4():
        return create_round_ui(input, "Midwest", 4, get_matchups_for_round(input, "Midwest", 4))

    @output
    @render.ui
    def final_four_games():
        return create_round_ui(input, "final", 5, get_final_four_matchups(input))

    @output
    @render.ui
    def championship_game():
        return create_round_ui(input, "final", 6, get_championship_matchup(input))

    # Bracket Assessment Output
    @output
    @render.ui
    def assessment_results():
        # Track changes in bracket selections
        bracket_selections = []
        for region in ["east", "west", "south", "midwest"]:
            # First round (8 games)
            for i in range(8):
                game_id = f"{region}_round1_game_{i}"
                try:
                    winner = input[game_id]()
                    if winner:
                        bracket_selections.append(f"{game_id}:{winner}")
                except:
                    pass
                    
            # Second round (4 games)
            for i in range(4):
                game_id = f"{region}_round2_game_{i}"
                try:
                    winner = input[game_id]()
                    if winner:
                        bracket_selections.append(f"{game_id}:{winner}")
                except:
                    pass
            
            # Sweet 16 (2 games)
            for i in range(2):
                game_id = f"{region}_round3_game_{i}"
                try:
                    winner = input[game_id]()
                    if winner:
                        bracket_selections.append(f"{game_id}:{winner}")
                except:
                    pass
            
            # Elite 8 (1 game)
            game_id = f"{region}_round4_game_0"
            try:
                winner = input[game_id]()
                if winner:
                    bracket_selections.append(f"{game_id}:{winner}")
            except:
                pass
        
        # Final Four (2 games)
        for i in range(2):
            game_id = f"final_round5_game_{i}"
            try:
                winner = input[game_id]()
                if winner:
                    bracket_selections.append(f"{game_id}:{winner}")
            except:
                pass
        
        # Championship (1 game)
        game_id = "final_round6_game_0"
        try:
            winner = input[game_id]()
            if winner:
                bracket_selections.append(f"{game_id}:{winner}")
        except:
            pass
        
        # Also use trigger from tab switch or pool size change
        try:
            input.__forceAssessmentUpdate__
        except:
            pass
        
        # React to pool size changes
        pool_size = input.pool_size()
            
        # Check if we have any selections
        if not bracket_selections:
            return ui.div(
                ui.p("Please make your bracket selections in the region tabs, then return here for an assessment.", 
                    class_="text-center text-muted mt-4")
            )
        
        # Process the assessment as before
        try:
            assessment = analyze_bracket(input)
            assessment_text = format_bracket_assessment(assessment, input)  # Pass input to get pool size
            html_content = markdown(assessment_text)
            return ui.HTML(html_content)
        except Exception as e:
            logger.error(f"Error in bracket assessment: {str(e)}", exc_info=True)
            return ui.p(f"Error assessing bracket: {str(e)}", class_="text-danger")
