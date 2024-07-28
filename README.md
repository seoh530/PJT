# 3D Coordinate Simulator

This project is a 3D coordinate simulator that shows the positions of head-mounted displays (HMD) and hand devices over time.
The simulator allows users to visualize the movement and orientation of these devices using animated 3D scatter plots.

## Features

- Animated 3D scatter plots to visualize the position of HMD and hand devices over time.
- Option to toggle between viewing animated points and viewing all movements connected by lines.
- Interactive timestamp slider to control the animation.

## Requirements

- Python
- Flask
- Pandas
- Plotly

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/3d-coordinate-simulator.git
    cd 3d-coordinate-simulator
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Create an `uploads` directory in the project folder if it does not exist:
    ```sh
    mkdir uploads
    ```

## Usage

1. Run the Flask app:
    ```sh
    python app.py
    ```

2. Open a web browser and go to `http://127.0.0.1:5000/`.

3. Upload your data file in the provided format.

4. Use the interactive slider to animate the 3D scatter plots and toggle between different views.
   

## Data File Format

The data file should be a text file with the following format

