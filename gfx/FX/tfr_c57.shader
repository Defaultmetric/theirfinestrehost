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
		// Screen cell (1,7) of an 8x8 grid. One texture is capped at 4096
		// by the engine (texturehandler.cpp MAX_TEXTURE_SIZE), so 64 windows each
		// carry a 4056x1496 atlas. Together: 438 frames of 1248x704 at 15 fps,
		// a 29.2 second loop. The source file is 1280x720, so this is its ceiling.
		float4 main( VS_OUTPUT input ) : PDX_COLOR
		{
			const float COLS   = 26.0;
			const float ROWS   = 17.0;
			const float FRAMES = 438.0;
			const float LOOP   = 29.2;
			const float2 CELL  = float2( 1.0, 7.0 );

			float f  = floor( frac( abs( Time ) / LOOP ) * FRAMES );
			float cy = floor( f / COLS );
			float cx = f - cy * COLS;

			float  w2  = max( abs( input.vScreenPos.w ), 0.00001 );
			float2 ndc = input.vScreenPos.xy / w2;
			float2 screenUV = float2( ndc.x * 0.5 + 0.5, -ndc.y * 0.5 + 0.5 );

			float2 frameUV = screenUV * 8.0 - CELL;

			float2 halfTexel = float2( 0.5 / 156.0, 0.5 / 88.0 );
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
