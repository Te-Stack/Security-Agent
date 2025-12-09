import asyncio
import os
import logging
import time
from vision_agents.core import agents, User
import vision_agents.plugins.getstream as getstream_plugin
from getstream import AsyncStream
from ultralytics import YOLO
import vision_agents.plugins.gemini as gemini

# Import the Pose Processor to inherit from (Fixes the "Video Track" compatibility)
from vision_agents.plugins.ultralytics import YOLOPoseProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityAgent")

class SecurityLogic(YOLOPoseProcessor):
    def __init__(self, call, model_name="yolov8n.pt", cooldown=5.0):
        # Initialize parent to establish the video track
        super().__init__(model=model_name, confidence=0.5)
        
        self.call = call
        self.cooldown = cooldown
        self.last_alert_time = 0
        
        # Load the detection model
        logger.info(f"Loading YOLO model: {model_name}...")
        self.model = YOLO(model_name) 

    async def process(self, frame, **kwargs):
        results = self.model(frame, verbose=False)
        annotated_frame = results[0].plot()

        # --- ULTRA SENSITIVE LOGIC ---
        # 1. Did we get ANY bounding box?
        has_box = len(results[0].boxes) > 0
        
        # 2. Did we get ANY keypoints?
        has_pose = False
        if hasattr(results[0], 'keypoints') and results[0].keypoints is not None:
            # Check if ANY point is visible (Confidence > 0.01)
            if results[0].keypoints.has_visible:
                has_pose = True

        # Trigger if EITHER is true
        if has_box or has_pose:
            now = time.time()
            if (now - self.last_alert_time > self.cooldown):
                print(f"\n🚨 INTRUDER DETECTED! 🚨", flush=True)
                
                try:
                    await self.call.client.video.send_call_event(
                        call_type="default",
                        call_id="security-demo-1",
                        event_content={
                            "type": "custom",
                            "custom_type": "intrusion_alert",
                            "data": {"message": "Person detected", "timestamp": now}
                        }
                    )
                    print("✅ Signal sent", flush=True)
                except Exception as e:
                    print(f"❌ Failed: {e}", flush=True)

                self.last_alert_time = now
        
        return annotated_frame

async def main():
    api_key = os.getenv("STREAM_API_KEY")
    api_secret = os.getenv("STREAM_API_SECRET")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not api_key or not gemini_key: 
        raise ValueError("❌ Missing API Keys in .env")

    # 1. Initialize Stream Client (Async)
    # FIX: Removed 'location="us-east"'
    client = AsyncStream(api_key=api_key, api_secret=api_secret)
    
    call_id = "security-demo-1"
    
    # Create the Call Object
    call = client.video.call("default", call_id)
    await call.get_or_create(data={
        "created_by": { "id": "security-bot", "name": "Security Bot", "role": "admin" }
    })
    
    logger.info(f"📹 Security Feed Active. Call ID: {call_id}")

    # 2. Initialize Edge & LLM
    # FIX: Removed 'location="us-east"'
    edge = getstream_plugin.Edge(api_key=api_key, api_secret=api_secret)
    llm = gemini.LLM(model="gemini-1.5-flash", api_key=gemini_key)
    bot_user = User(id="security_agent", name="Security Guard")

    # 3. Initialize Logic
    security_processor = SecurityLogic(call=call)

    # 4. Create Agent
    agent = agents.Agent(
        edge=edge,
        llm=llm,
        agent_user=bot_user,
        processors=[security_processor]
    )

    logger.info("🤖 Agent is starting... Join the call in your browser!")
    
    # 5. Join and Run
    await agent.join(call)
    
    # Keep the script running
    logger.info("Agent running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Stopping agent...")

if __name__ == "__main__":
    asyncio.run(main())