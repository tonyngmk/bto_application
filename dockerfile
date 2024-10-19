# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set environment variables (optional)
# ENV SUPABASE_URL=your_supabase_url
# ENV SUPABASE_KEY=your_supabase_key

# Expose the port your app runs on (default for Flask is 5000)
EXPOSE 5000

# Command to run your app
CMD ["python", "app.py"]