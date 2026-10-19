# Step 1: Base Image - Official lightweight Python 3.12/3.14 slim Debian                                                              
FROM python:3.12-slim                                                                                                                 
                                                                                                                                        
# Step 2: Prevent Python from writing .pyc files and buffer stdout/stderr                                                             
ENV PYTHONDONTWRITEBYTECODE=1 \                                                                                                       
    PYTHONUNBUFFERED=1                                                                                                                
                                                                                                                                        
# Step 3: Set container working directory                                                                                             
WORKDIR /app                                                                                                                          
                                                                                                                                        
# Step 4: Install system dependencies required for compilation and MySQL/ONNX libraries                                               
RUN apt-get update && apt-get install -y --no-install-recommends \                                                                    
    build-essential \                                                                                                                 
    curl \                                                                                                                            
    default-libmysqlclient-dev \                                                                                                      
    pkg-config \                                                                                                                      
    && rm -rf /var/lib/apt/lists/*                                                                                                    
                                                                                                                                        
# Step 5: Copy dependency manifests first to leverage Docker layer caching                                                            
COPY requirements.txt .                                                                                                               
                                                                                                                                        
# Step 6: Install Python dependencies                                                                                                 
RUN pip install --no-cache-dir --upgrade pip && \                                                                                     
    pip install --no-cache-dir -r requirements.txt                                                                                    
                                                                                                                                        
# Step 7: Copy application source code                                                                                                
COPY . .                                                                                                                              
                                                                                                                                        
# Step 8: Create a non-root system user for enterprise security                                                                       
RUN useradd -m -u 1000 appuser && \                                                                                                   
    chown -R appuser:appuser /app                                                                                                     
                                                                                                                                        
# Step 9: Switch to non-root user                                                                                                     
USER appuser                                                                                                                          
                                                                                                                                        
# Step 10: Expose FastAPI internal application port                                                                                   
EXPOSE 8000                                                                                                                           
                                                                                                                                        
# Step 11: Production ASGI Server Startup Command                                                                                     
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]