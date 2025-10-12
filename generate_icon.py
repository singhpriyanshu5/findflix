import asyncio
import os
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

async def generate_findflix_icon():
    """Generate a FindFlix app icon using AI"""
    
    # Use the universal key
    api_key = "sk-emergent-c21A48b819eDb2720C"
    
    # Initialize image generator
    image_gen = OpenAIImageGeneration(api_key=api_key)
    
    # Prompt for FindFlix icon
    prompt = """Create a modern, minimalist app icon for 'FindFlix', a movie discovery app. 
    Design specifications:
    - Square format (1024x1024)
    - Clean, simple design that works at small sizes
    - Dark background (black or very dark gray)
    - Bold 'FF' letters in bright red (#e50914) as the main element
    - Modern, sleek typography
    - Slight gradient or subtle texture for depth
    - Professional app icon style similar to Netflix or streaming services
    - The icon should be iconic and recognizable when scaled down to 60x60 pixels
    - Minimal details, maximum impact
    """
    
    print("🎨 Generating FindFlix icon...")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        # Generate the icon
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            print("✅ Icon generated successfully!")
            
            # Save to the correct locations
            icon_paths = [
                '/app/frontend/assets/images/icon.png',
                '/app/frontend/assets/images/favicon.png',
                '/app/frontend/assets/images/adaptive-icon.png',
                '/app/frontend/public/icon.png',
                '/app/frontend/public/favicon.png'
            ]
            
            for path in icon_paths:
                # Ensure directory exists
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Save the image
                with open(path, 'wb') as f:
                    f.write(images[0])
                print(f"✅ Saved to: {path}")
            
            print("\n🎉 FindFlix icon created and saved to all required locations!")
            return True
        else:
            print("❌ No image was generated")
            return False
            
    except Exception as e:
        print(f"❌ Error generating icon: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(generate_findflix_icon())
