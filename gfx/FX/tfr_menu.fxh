VertexStruct VS_INPUT
{
	float3 vPosition  : POSITION;
	float2 vTexCoord  : TEXCOORD0;
};

ConstantBuffer( 0, 0 )
{
	float4x4 WorldViewProjectionMatrix;
	float4 Color;
	float2 Offset;
	float2 NextOffset;
	float Time;
	float AnimationTime;
};

Code
[[
	// ( Time - AnimationTime ) is meant to be the age of this element in
	// seconds. If it ever comes back as nonsense, everything below has to
	// degrade into "intro already finished" rather than "intro stuck at 0".
	#define TFR_INTRO_MAX   6.0    // past this the intro is considered over
	#define TFR_SWEEP_START 0.70   // when the light enters the screen
	#define TFR_SWEEP_LEN   1.20   // how long it takes to cross
	#define TFR_QUAD_RATIO  0.5    // wordmark quad is 2:1
	#define TFR_AMBIENT     9.0    // seconds between idle light passes
]]
