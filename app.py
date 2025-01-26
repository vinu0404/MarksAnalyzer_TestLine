from flask import Flask, request, render_template, redirect, url_for,make_response
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the JSON URL from the form
        json_url = request.form.get("json_url")
        
        # Fetch JSON data
        try:
            response = requests.get(json_url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return f"Error fetching JSON data: {e}"

        # Convert JSON data to a DataFrame
        df = pd.DataFrame(data)
        
        # Data preprocessing
        df['quiz_title'] = df['quiz'].apply(lambda x: x.get('title') if isinstance(x, dict) else None)
        df['quiz_topic'] = df['quiz'].apply(lambda x: x.get('topic') if isinstance(x, dict) else None)
        df['quiz_info'] = df['quiz_title'] + " - " + df['quiz_topic']

        # Generate and save plots
        plots = generate_plots(df)

        return render_template("index.html", plots=plots)

    return render_template("index.html")


def generate_plots(df):
    """Generates the plots and returns them as base64-encoded images."""
    plots = []

    # Plot 1: Incorrect and Correct Answers by Topic
    melted_df = pd.melt(df, id_vars=['quiz_topic'], 
                        value_vars=['incorrect_answers', 'correct_answers'], 
                        var_name='Answer Type', value_name='Count')
    plt.figure(figsize=(12, 6))
    sns.barplot(x='quiz_topic', y='Count', hue='Answer Type', data=melted_df)
    plt.title('Incorrect and Correct Answers by Topic')
    plt.xlabel('Topic')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plots.append(encode_plot_as_base64())

    # Plot 2: Initial Mistakes and Mistakes Corrected by Topic
    melted_df = pd.melt(df, id_vars=['quiz_topic'], 
                        value_vars=['initial_mistake_count', 'mistakes_corrected'], 
                        var_name='Mistake Type', value_name='Count')
    plt.figure(figsize=(12, 6))
    sns.barplot(x='quiz_topic', y='Count', hue='Mistake Type', data=melted_df)
    plt.title('Initial Mistakes and Mistakes Corrected by Topic')
    plt.xlabel('Topic')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plots.append(encode_plot_as_base64())

    # Plot 3: Score by Topic
    plt.figure(figsize=(10, 6))
    sns.barplot(x='quiz_topic', y='score', data=df, palette="viridis")
    plt.title('Score by Topic')
    plt.xlabel('Topic')
    plt.ylabel('Score')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plots.append(encode_plot_as_base64())

    # Plot 4: Better Than by Topic
    plt.figure(figsize=(10, 6))
    sns.barplot(x='quiz_topic', y='better_than', data=df)
    plt.title('Better Than by Topic')
    plt.xlabel('Topic')
    plt.ylabel('Better Than')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plots.append(encode_plot_as_base64())


    
    temp_df = df.copy()

    # Ensure numeric values
    temp_df['correct_answers'] = pd.to_numeric(temp_df['correct_answers'], errors='coerce')
    temp_df['incorrect_answers'] = pd.to_numeric(temp_df['incorrect_answers'], errors='coerce')

    # Calculate accuracy if not already present
    if 'accuracy' in temp_df.columns:
        temp_df['accuracy'] = (temp_df['correct_answers'] / 
                            (temp_df['correct_answers'] + temp_df['incorrect_answers']) * 100)

    # Ensure accuracy is numeric
    temp_df['accuracy'] = pd.to_numeric(temp_df['accuracy'], errors='coerce')

    # Drop rows with NaN values in required columns
    temp_df = temp_df.dropna(subset=['correct_answers', 'incorrect_answers', 'accuracy'])

    # Aggregate data by quiz_topic
    performance_df = temp_df.groupby('quiz_info', as_index=False).agg({
        'accuracy': 'mean',
        'correct_answers': 'sum',
        'incorrect_answers': 'sum'
    })

    # Create grouped bar chart
    x = np.arange(len(performance_df['quiz_info']))  # Topic indices
    width = 0.3  # Width of each bar

    plt.figure(figsize=(12, 6))
    
    # Plot metrics
    plt.bar(x - width, performance_df['accuracy'], width, label='Accuracy (%)', color='blue')
    plt.bar(x, performance_df['correct_answers'], width, label='Correct Answers', color='green')
    plt.bar(x + width, performance_df['incorrect_answers'], width, label='Incorrect Answers', color='red')
    
    # Customize the plot
    plt.xlabel('Quiz Topic')
    plt.ylabel('Metrics')
    plt.title('Quiz Performance by Topic (Grouped Bar Chart)')
    plt.xticks(x, performance_df['quiz_info'], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()

    # Show the plot
    
    plots.append(encode_plot_as_base64())

    
    return plots





def encode_plot_as_base64():
    """Encodes the current Matplotlib plot as a base64 string."""
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    base64_img = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return base64_img



if __name__ == "__main__":
    app.run(debug=True)



















