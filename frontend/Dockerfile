 # ==========================================                                                                                          
# STAGE 1: Compile Angular Application                                                                                                
# ==========================================                                                                                          
FROM node:20-alpine AS builder                                                                                                        
                                                                                                                                        
WORKDIR /app                                                                                                                          
                                                                                                                                        
# Copy dependency manifests first for layer caching                                                                                   
COPY package.json package-lock.json ./                                                                                                
                                                                                                                                        
# Clean installation of dependencies                                                                                                  
RUN npm ci                                                                                                                            
                                                                                                                                        
# Copy frontend source code                                                                                                           
COPY . .                                                                                                                              
                                                                                                                                        
# Compile production bundle                                                                                                           
RUN npm run build -- --configuration production                                                                                       
                                                                                                                                        
# ==========================================                                                                                          
# STAGE 2: Lightweight Nginx Production Server                                                                                        
# ==========================================                                                                                          
FROM nginx:alpine                                                                                                                     
                                                                                                                                        
# Remove default Nginx welcome site                                                                                                   
RUN rm -rf /usr/share/nginx/html/*                                                                                                    
                                                                                                                                        
# Copy compiled static output from Stage 1 builder                                                                                    
# Note: Angular builds to dist/frontend/browser                                                                                       
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html                                                                  
                                                                                                                                        
# Copy custom Nginx SPA routing and reverse proxy configuration                                                                       
COPY nginx.conf /etc/nginx/conf.d/default.conf                                                                                        
                                                                                                                                        
# Expose HTTP port 80                                                                                                                 
EXPOSE 80                                                                                                                             
                                                                                                                                        
# Start Nginx in foreground                                                                                                           
CMD ["nginx", "-g", "daemon off;"]