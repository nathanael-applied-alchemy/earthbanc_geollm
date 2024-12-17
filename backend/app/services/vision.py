# backend/app/services/vision.py

from typing import Dict, Any
import asyncio
import traceback
import anthropic


class VisionService:
    def __init__(self, anthropic_api_key: str):
        self.anthropic_api_key = anthropic_api_key

    async def analyze(self, sentinel_data: Dict[str, Any]) -> Dict[str, Any]:

        pass

    async def analyze_land(
        self,
        weather_data: Dict,
        soil_data: Dict,
        location_data: Dict,
        image_data: str
    ) -> Dict:
        """
        Analyze land suitability using Claude
        """

        weather_prompt = ""
    #     weather_prompt += f"""
    #     Weather Data:
    # - Rainfall: {weather_data.get('rainfall_mm')}mm
    # - Temperature: {weather_data.get('temperature_celsius')}°C
    # - Wind Speed: {weather_data.get('wind_speed_kph')}kph
    # """

        soil_prompt = ""
    #     soil_prompt += f"""
    # Soil Data:
    # - pH Level: {soil_data.get('ph')}
    # - Organic Carbon: {soil_data.get('organic_carbon')}%
    # - Moisture: {soil_data.get('moisture_percent')}%
    # """

        location_prompt = ""
        
    #     location_prompt += f"""
    # Location:
    # - Latitude: {location_data.get('latitude')}
    # - Longitude: {location_data.get('longitude')}
    # """

        prompt = f"""Given the following image and data about a piece of land, analyze its suitability for agriculture and provide recommendations:

    {weather_prompt}\n
    {soil_prompt}\n
    {location_prompt}\n

    Please provide:
    1. A suitability score from 0-1
    2. A list of specific recommendations for agricultural use
    3. Key considerations for crop selection
    """

        try:

            # Call Claude API
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2500,
                messages=[
                    # {"role": "user", "content": prompt}

                    {"role": "user", "content": [
                        {
                            "type": "image",
                            "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                            }
                        },
                        {"type": "text", "text": prompt}
                        ]}
                ]
            )
            
            # Parse the response and extract key information
            analysis_text = response.content[0].text
                        
            return {
                "analysis": analysis_text,
                "recommendations": [rec.strip() for rec in analysis_text.split("\n") if rec.strip().startswith("-")]
            }

        except Exception as e:
            print(f"Error in LLM analysis: {str(e)}")
            return {
                "analysis": "Error in LLM analysis",
                "recommendations": []
            }
