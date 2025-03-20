#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   ui.py
@Time    :   2024/02/20
@Author  :   Taylor Firman
@Version :   1.0
@Contact :   tefirman@gmail.com
@Desc    :   UI components for March Madness bracket app
'''

from shiny import ui

def create_round_header(round_name: str) -> ui.tags.h4:
    """Create a header for a tournament round"""
    return ui.h4(round_name, class_="mt-4 mb-3")

def create_region_column(region: str) -> ui.div:
    """Create a div containing a region's bracket with horizontal round layout"""
    return ui.div(
        ui.h3(f"{region} Region", class_="region-title"),
        ui.row(
            ui.column(
                3,  # Each round takes 1/4 of the width
                create_round_header("First Round"),
                ui.output_ui(f"{region.lower()}_bracket_round1"),
                class_="round-column"
            ),
            ui.column(
                3,
                create_round_header("Second Round"),
                ui.output_ui(f"{region.lower()}_bracket_round2"),
                class_="round-column"
            ),
            ui.column(
                3,
                create_round_header("Sweet 16"),
                ui.output_ui(f"{region.lower()}_bracket_round3"),
                class_="round-column"
            ),
            ui.column(
                3,
                create_round_header("Elite Eight"),
                ui.output_ui(f"{region.lower()}_bracket_round4"),
                class_="round-column"
            ),
            class_="region-rounds"
        ),
        class_="region-container"
    )

def create_final_rounds() -> ui.div:
    """Create a div containing the Final Four and Championship rounds"""
    return ui.div(
        ui.h3("Final Rounds", class_="text-center mb-4"),
        ui.row(
            ui.column(
                6,
                create_round_header("Final Four"),
                ui.output_ui("final_four_games")
            ),
            ui.column(
                6,
                create_round_header("Championship"),
                ui.output_ui("championship_game")
            ),
            class_="final-rounds"
        ),
        class_="final-rounds-container"
    )

# Custom CSS for bracket styling
custom_css = """
.region-container {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 20px;
}

.region-title {
    margin-bottom: 20px;
}

.round-column {
    border-right: 1px solid #eee;
    padding: 0 10px;
    min-height: 600px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.round-column:last-child {
    border-right: none;
}

.bracket-region {
    display: flex;
    flex-direction: column;
}

.game-container {
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 5px;
}

/* First round games are close together */
.round-column:nth-child(1) .game-container {
    margin-bottom: 15px;
}

/* Second round games have more space */
.round-column:nth-child(2) .game-container {
    margin-bottom: 60px;
    margin-top: 30px;
}

/* Sweet 16 games have even more space */
.round-column:nth-child(3) .game-container {
    margin-bottom: 140px;
    margin-top: 70px;
}

/* Elite Eight game is centered in its column */
.round-column:nth-child(4) .game-container {
    margin-top: 0;  /* Remove top margin and let flex centering handle it */
}

.game-container .shiny-input-container {
    margin-bottom: 0;
}

.bracket-region {
    background-color: white;
}

.region-rounds {
    margin: 0;
}

/* Make sure radio buttons and labels don't wrap awkwardly */
.game-container .form-check {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Assessment results styling */
.assessment-results {
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif;
    line-height: 1.5;
    white-space: pre-wrap;
    background-color: #f8f9fa;
    border-radius: 5px;
    padding: 15px;
    margin-top: 15px;
    border-left: 4px solid #0d6efd;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

.assessment-results h1 {
    font-size: 1.75rem;
    margin-bottom: 1rem;
    color: #0d6efd;
}

.assessment-results h2 {
    font-size: 1.5rem;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: #495057;
}

.assessment-results h3 {
    font-size: 1.25rem;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    color: #6c757d;
}

.assessment-results ul, .assessment-results ol {
    margin-bottom: 1rem;
    padding-left: 2rem;
}

/* Custom Region Selector Styling */
.region-selector {
    display: flex;
    flex-direction: row;
    margin-bottom: 20px;
    border-bottom: 1px solid #dee2e6;
    background-color: #f8f9fa;
    border-radius: 5px 5px 0 0;
    overflow: hidden;
}

.region-selector button {
    flex: 1;
    padding: 12px 15px;
    border: none;
    background: none;
    font-weight: 500;
    color: #495057;
    cursor: pointer;
    transition: background-color 0.2s;
    position: relative;
}

.region-selector button:hover {
    background-color: #e9ecef;
}

.region-selector button.active {
    background-color: #fff;
    color: #0d6efd;
    border-bottom: 2px solid #0d6efd;
}

.region-selector button.active:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background-color: #0d6efd;
}

.region-content {
    position: absolute;
    width: 100%;
    padding: 15px;
    border: 1px solid #dee2e6;
    border-top: none;
    border-radius: 0 0 5px 5px;
    background-color: #fff;
    transition: opacity 0.3s ease;
    z-index: 1; /* Default z-index */
    pointer-events: none; /* Disable pointer events by default */
}

.region-content.active {
    z-index: 10; /* Higher z-index for active tab */
    pointer-events: auto; /* Enable pointer events for active tab */
}

/* Container for region content to maintain stable height */
.region-container-wrapper {
    position: relative;
    min-height: 700px; /* Adjust this value based on the tallest content */
    margin-bottom: 20px;
}

/* Styling for assessment tab */
#assessment-region {
    padding: 30px;
}

/* Pool size selector styling */
.pool-size-selector {
    text-align: center;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: #f8f9fa;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.pool-size-selector label {
    font-weight: 500;
    margin-right: 1rem;
}

.pool-size-selector select {
    min-width: 100px;
}
"""

# JavaScript for region selector tabs
region_tabs_js = """
$(document).ready(function() {
    // Initially hide all content except the first one
    $(".region-content").removeClass("active").css('opacity', '0');
    $("#east-region").addClass("active").css('opacity', '1');
    
    // Set the first tab as active
    $("#east-tab").addClass("active");
    
    // Handle tab clicks
    $(".region-selector button").click(function() {
        // Remove active class from all tabs
        $(".region-selector button").removeClass("active");
        
        // Add active class to clicked tab
        $(this).addClass("active");
        
        // Hide all region content and disable interactions
        $(".region-content").removeClass("active").css('opacity', '0');
        
        // Show the selected region content and enable interactions
        var regionId = $(this).attr("data-region");
        $("#" + regionId + "-region").addClass("active").css('opacity', '1');

        // If switching to assessment tab, trigger Shiny to re-render the assessment
        if ($(this).attr("data-region") === "assessment") {
            // Force Shiny to recalculate the assessment output
            Shiny.setInputValue('__forceAssessmentUpdate__', Math.random());
        }
    });
});
"""

# Create main app UI
app_ui = ui.page_fluid(
    # Add custom CSS
    ui.tags.style(custom_css),
    
    # Add jQuery for our tab functionality (if not already included by Shiny)
    ui.tags.script(src="https://code.jquery.com/jquery-3.6.0.min.js"),
    
    # Add our custom JavaScript
    ui.tags.script(region_tabs_js),
    
    # App header
    ui.div(
        ui.h2("March Madness Bracket Creator", class_="text-center mb-4"),
        class_="container-fluid"
    ),
    
    # Pool size selector
    ui.div(
        ui.div(
            ui.tags.label("Pool Size: ", **{"for": "pool_size"}),
            ui.input_select(
                "pool_size",
                "",  # No label, as we're using the label tag above
                choices={
                    "10": "10 Entries",
                    "100": "100 Entries"
                },
                selected="100"
            ),
            class_="pool-size-selector"
        )
    ),
    
    # Main layout - removed sidebar, made it full width
    ui.div(
        ui.div(
            # Region selector tabs
            ui.div(
                ui.tags.button("East Region", id="east-tab", **{"data-region": "east", "class": "region-tab"}),
                ui.tags.button("West Region", id="west-tab", **{"data-region": "west", "class": "region-tab"}),
                ui.tags.button("South Region", id="south-tab", **{"data-region": "south", "class": "region-tab"}),
                ui.tags.button("Midwest Region", id="midwest-tab", **{"data-region": "midwest", "class": "region-tab"}),
                ui.tags.button("Final Rounds", id="finals-tab", **{"data-region": "finals", "class": "region-tab"}),
                ui.tags.button("Assessment", id="assessment-tab", **{"data-region": "assessment", "class": "region-tab"}),
                class_="region-selector"
            ),
            
            # Region content wrapper with fixed height
            ui.div(
                # Region content - all absolutely positioned within the wrapper
                ui.div(create_region_column("East"), id="east-region", class_="region-content"),
                ui.div(create_region_column("West"), id="west-region", class_="region-content"),
                ui.div(create_region_column("South"), id="south-region", class_="region-content"),
                ui.div(create_region_column("Midwest"), id="midwest-region", class_="region-content"),
                ui.div(create_final_rounds(), id="finals-region", class_="region-content"),
                ui.div(
                    ui.h3("Bracket Assessment", class_="text-center mb-4"),
                    ui.p("Analysis of your bracket selections based on historical tournament data:"),
                    ui.div(
                        ui.output_ui("assessment_results"),  # Changed from output_text to output_ui
                        class_="assessment-results"
                    ),
                    id="assessment-region", 
                    class_="region-content"
                ),
                class_="region-container-wrapper"
            ),
        ),
        
        # Footer
        ui.div(
            ui.p(
                "Created by Taylor Firman. See ",
                ui.a("GitHub", href="https://github.com/tefirman/bigdance"),
                " for more details.",
                class_="text-center text-muted small"
            ),
            class_="mt-4"
        )
    )
)
