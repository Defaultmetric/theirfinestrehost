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
		// 84 frames of 576x324 packed 7 across, 12 down. The atlas is 4032x3888
		// because the engine refuses any texture over 4096 (texturehandler.cpp
		// MAX_TEXTURE_SIZE), which caps total pixels and therefore frame count.
		// 10 fps off the engine Time uniform: an 8.4 second loop.
		float4 main( VS_OUTPUT input ) : PDX_COLOR
		{
			const float COLS   = 7.0;
			const float ROWS   = 12.0;
			const float FRAMES = 84.0;
			const float LOOP   = 8.4;

			float f  = floor( frac( abs( Time ) / LOOP ) * FRAMES );
			float cy = floor( f / COLS );
			float cx = f - cy * COLS;

			// The background quad is 1920x1440 scaled to cover the screen, so its
			// own vTexCoord does not line up with what is actually visible. Going
			// through normalised device coords instead maps one video frame onto
			// exactly the viewport, whatever the quad is doing.
			float  w2 = max( abs( input.vScreenPos.w ), 0.00001 );
			float2 ndc = input.vScreenPos.xy / w2;
			float2 frameUV = float2( ndc.x * 0.5 + 0.5, -ndc.y * 0.5 + 0.5 );

			// half texel of one tile, so bilinear never samples the next frame
			float2 halfTexel = float2( 0.5 / 576.0, 0.5 / 324.0 );
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

# Without these the engine binds no effect at all and just blits the raw
# texture, which is why the whole atlas showed up on screen at once.
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
