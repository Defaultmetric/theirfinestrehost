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
	#define TFR_CYCLE      4.6      // full loop length in seconds
	#define TFR_SWEEP      0.85     // how long the light takes to cross
	#define TFR_FADE_START 3.85     // when the letters start fading back to black
	#define TFR_FADE_END   4.45
	#define TFR_QUAD_RATIO 0.5      // texture is 2:1, so 1 unit of v = 0.5 units of u on screen
]]
