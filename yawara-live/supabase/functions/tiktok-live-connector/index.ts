// Yawara Live — receiver for documented TikTok developer webhooks.
// LIVE gift/like/share/comment event APIs have NOT been verified or enabled.
// TikTok client_secret must be configured via Supabase Edge Function secrets.
// No events here are used to award points.
const known = new Set(["authorization.removed","video.upload.failed","video.publish.completed","portability.download.ready"]);
const json=(code:number,value:unknown)=>new Response(JSON.stringify(value),{status:code,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
function safeEqual(a:string,b:string){if(a.length!==b.length)return false;let diff=0;for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^b.charCodeAt(i);return diff===0;}
async function validTikTokSignature(raw:string,header:string,secret:string){
  const pairs=Object.fromEntries(header.split(",").map(x=>x.trim().split("=")).filter(x=>x.length===2));
  const ts=pairs.t,sig=pairs.s;
  if(!ts||!sig||!/^[0-9]{10,13}$/.test(ts)||!/^[0-9a-f]{64}$/i.test(sig))return false;
  const stamp=Number(ts);if(!Number.isSafeInteger(stamp)||Math.abs(Date.now()/1000-stamp)>300)return false;
  const hmac=await crypto.subtle.importKey("raw",new TextEncoder().encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const digest=new Uint8Array(await crypto.subtle.sign("HMAC",hmac,new TextEncoder().encode(ts+"."+raw)));
  const expected=Array.from(digest,x=>x.toString(16).padStart(2,"0")).join("");
  return safeEqual(expected,sig.toLowerCase());
}
Deno.serve(async(req:Request)=>{
  if(req.method==="GET")return json(200,{project:"yawara-live",receiver:"tiktok-developer-webhook",configured:Boolean(Deno.env.get("TIKTOK_CLIENT_SECRET")),live_events_supported:false,scoring_enabled:false});
  if(req.method!=="POST")return json(405,{error:"method_not_allowed"});
  const secret=Deno.env.get("TIKTOK_CLIENT_SECRET");
  const expectedClientKey=Deno.env.get("TIKTOK_CLIENT_KEY");
  if(!secret||!expectedClientKey)return json(503,{error:"tiktok_developer_credentials_not_configured"});
  if(Number(req.headers.get("content-length")||0)>65536)return json(413,{error:"payload_too_large"});
  let raw="";try{raw=await req.text()}catch{return json(400,{error:"body_unavailable"})}
  if(raw.length>65536)return json(413,{error:"payload_too_large"});
  if(!await validTikTokSignature(raw,req.headers.get("TikTok-Signature")||"",secret))return json(401,{error:"invalid_signature"});
  let event:any;try{event=JSON.parse(raw)}catch{return json(400,{error:"invalid_json"})}
  if(event?.client_key!==expectedClientKey)return json(403,{error:"invalid_client_key"});
  if(!known.has(event?.event))return json(202,{accepted:false,reason:"unsupported_event_type",scoring_enabled:false});
  // Recognized TikTok developer events are NOT TikTok LIVE interactions.
  // Production processing, secure storage, and deauthorization handling
  // must be implemented only for approved scopes/use cases.
  return json(200,{received:true,event:event.event,live_scoring:false});
});
