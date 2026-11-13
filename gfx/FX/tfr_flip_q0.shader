Includes = {
	"tfr_flipbook.fxh"
}
PixelShader =
{
	Samplers =
	{
		MapTexture =
		{
			Index = 0
			MagFilter = "Linear"
			MinFilter = "Linear"
			MipFilter = "Linear"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}
VertexStruct VS_OUTPUT
{
	float4 vPosition   : PDX_POSITION;
	float2 vTexCoord   : TEXCOORD0;
	float4 vScreenPos  : TEXCOORD1;
};
VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main( const VS_INPUT v )
		{
			VS_OUTPUT Out;
			Out.vPosition = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1 ) );
			Out.vTexCoord = v.vTexCoord;
			Out.vScreenPos = Out.vPosition;
			return Out;
		}
	]]
}
PixelShader =
{
	MainCode PixelShaderFlipbook
	[[
		// Screen quadrant 0 of 4. Each quadrant carries its own 4032x4032
		// atlas, because a single texture is capped at 4096 by the engine
		// (texturehandler.cpp MAX_TEXTURE_SIZE). Four of them together give a
		// 896x504 frame held for 144 frames instead of the ~84 one texture allows.
		// 9 across, 16 down, 12 fps: a 12 second loop.
		float4 main( VS_OUTPUT input ) : PDX_COLOR
		{
			const float COLS   = 9.0;
			const float ROWS   = 16.0;
			const float FRAMES = 144.0;
			const float LOOP   = 12.0;
			const float2 QUAD  = float2( 0.0, 0.0 );

			float f  = floor( frac( abs( Time ) / LOOP ) * FRAMES );
			float cy = floor( f / COLS );
			float cx = f - cy * COLS;

			// Normalised device coords give the position on the SCREEN, which is
			// what we need: the parent background quad is 1920x1440 scaled to
			// cover, so it overflows the viewport and its own UVs are useless.
			float  w2  = max( abs( input.vScreenPos.w ), 0.00001 );
			float2 ndc = input.vScreenPos.xy / w2;
			float2 screenUV = float2( ndc.x * 0.5 + 0.5, -ndc.y * 0.5 + 0.5 );

			// This container covers one screen quadrant, so stretch that quadrant
			// back out to the full 0..1 range of its own atlas tile.
			float2 frameUV = screenUV * 2.0 - QUAD;

			float2 halfTexel = float2( 0.5 / 448.0, 0.5 / 252.0 );
			float2 tile = clamp( saturate( frameUV ), halfTexel, 1.0 - halfTexel );

			float2 uv = ( tile + float2( cx, cy ) ) / float2( COLS, ROWS );
			return float4( tex2D( MapTexture, uv ).rgb, 1.0 );
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}

Effect Up
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderFlipbook"
}
Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderFlipbook"
}
Effect Disable
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderFlipbook"
}
Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderFlipbook"
}
