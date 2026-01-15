import asyncio
import os
import time
import logging
import sys
from vision_agents.core import agents, User
import vision_agents.plugins.getstream as getstream_plugin
from getstream import AsyncStream
from vision_agents.plugins.ultralytics import YOLOPoseProcessor
from ultralytics import YOLO
import vision_agents.plugins.gemini as gemini


logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)


print("\n🚀 SECURITY DASHBOARD - ARGUMENT ORDER FIX\n", flush=True)


# --- GLOBAL VARIABLES ---
ACTIVE_CALL_ID = "security-demo-working"
STREAM_CLIENT = None


class SecurityYOLOProcessor(YOLOPoseProcessor):
    def __init__(self, model="yolo11n-pose.pt", confidence=0.5, cooldown=5.0):
        super().__init__(model=model, confidence=confidence)
        self.cooldown = cooldown
        self.last_alert_time = 0
        self.frame_count = 0
       
        print("📦 Loading detection model...", flush=True)
        self.detect_model = YOLO("yolo11n.pt")
        print("✅ Processor Ready", flush=True)
   
    async def _process_pose_async(self, frame_data):
        # 1. Parent Logic
        annotated = await super()._process_pose_async(frame_data)
       
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            print(f"💓 Frame {self.frame_count}", flush=True)
       
        # 2. Detection Logic
        try:
            if self.frame_count % 5 == 0:
                results = self.detect_model(frame_data, verbose=False)
                person_count = 0
                for box in results[0].boxes:
                    if int(box.cls) == 0:
                        person_count += 1
               
                if person_count > 0:
                    await self._send_alert(person_count)
        except Exception as e:
            pass
       
        return annotated
   
    async def _send_alert(self, person_count):
        now = time.time()
       
        if (now - self.last_alert_time) > self.cooldown:
            print(f"\n🚨 {person_count} PERSON(S) DETECTED! Sending Alert...", flush=True)
           
            try:
                if STREAM_CLIENT:
                    # 🛠️ FIX: SIMPLE FLAT PAYLOAD
                    # We don't try to nest "custom" inside "custom".
                    # We just send the data directly.
                    payload = {
                        "alert_trigger": "intrusion", # <--- The Key we will look for
                        "message": f"{person_count} Intruder(s) Detected",
                        "person_count": person_count,
                        "timestamp": now
                    }


                    await STREAM_CLIENT.video.send_call_event(
                        "default",         # Call Type
                        ACTIVE_CALL_ID,    # Call ID
                        "security_agent",  # User ID
                        payload            # The Data
                    )
                   
                    print(f"✅ ALERT SENT!", flush=True)
                else:
                    print(f"❌ CRITICAL: Global CLIENT variable is missing!", flush=True)
               
                self.last_alert_time = now
               
            except Exception as e:
                print(f"❌ Alert Failed: {e}", flush=True)


async def main():
    global STREAM_CLIENT
   
    api_key = os.getenv("STREAM_API_KEY")
    api_secret = os.getenv("STREAM_API_SECRET")
    gemini_key = os.getenv("GEMINI_API_KEY")


    if not api_key: raise ValueError("❌ Check .env")


    client = AsyncStream(api_key=api_key, api_secret=api_secret)
    STREAM_CLIENT = client
   
    call = client.video.call("default", ACTIVE_CALL_ID)
    await call.get_or_create(data={"created_by": {"id": "security-bot"}})
   
    print(f"📹 Call ID: {ACTIVE_CALL_ID}", flush=True)
   
    processor = SecurityYOLOProcessor(
        model="yolo11n-pose.pt",
        confidence=0.5,
        cooldown=5.0
    )
   
    edge = getstream_plugin.Edge(api_key=api_key, api_secret=api_secret)
    llm = gemini.LLM(model="gemini-1.5-flash", api_key=gemini_key)
   
    agent = agents.Agent(
        edge=edge,
        llm=llm,
        agent_user=User(id="security_agent", name="Security Guard"),
        processors=[processor]
    )
   
    print("🤖 Agent joining...", flush=True)
    await agent.join(call)
    print("✅ AGENT LIVE!", flush=True)
   
    try:
        while True: await asyncio.sleep(1)
    except KeyboardInterrupt: pass


if __name__ == "__main__":
    asyncio.run(main())
