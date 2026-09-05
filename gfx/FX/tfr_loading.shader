# TFR animated loading screen.
# A light sweeps left to right, revealing the letters as it passes and dragging
# their shadows along behind it. Everything else stays black.
Includes = {
	"tfr_loading.fxh"
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
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}

VertexStruct VS_OUTPUT
{
	float4  vPosition : PDX_POSITION;
	float2  vTexCoord : TEXCOORD0;
};

VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main( const VS_INPUT v )
		{
			VS_OUTPUT Out;
			Out.vPosition = mul( WorldViewProjectionMatrix, float4( v.vPosition.xyz, 1 ) );
			Out.vTexCoord = v.vTexCoord + Offset;
			return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelShaderTFRLoading
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float2 uv = v.vTexCoord;

			// ---- timing -------------------------------------------------
			float t = frac( Time / TFR_CYCLE ) * TFR_CYCLE;

			float sweep = saturate( t / TFR_SWEEP );
			sweep = sweep * sweep * ( 3.0 - 2.0 * sweep );          // ease in/out
			float lightX = -0.22 + sweep * 1.44;                    // off-screen left -> off-screen right

			float fade = 1.0 - smoothstep( TFR_FADE_START, TFR_FADE_END, t );

			// ---- how much of the word the light has uncovered ------------
			float reveal = 1.0 - smoothstep( lightX - 0.015, lightX + 0.075, uv.x );

			// ---- the bulb ------------------------------------------------
			float2 d = uv - float2( lightX, 0.5 );
			d.y *= TFR_QUAD_RATIO;
			float dist2 = dot( d, d );

			float halo = exp( -dist2 * 11.0 );
			float core = exp( -dist2 * 900.0 );

			// ---- shadows cast away from the bulb -------------------------
			float2 dir = normalize( uv - float2( lightX, 0.5 ) + float2( 0.0001, 0.0 ) );
			float2 stp = dir * 0.011;

			float sh = 0.0;
			sh = max( sh, tex2D( MapTexture, uv - stp * 1.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 2.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 3.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 4.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 5.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 6.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 7.0 ).a );
			sh = max( sh, tex2D( MapTexture, uv - stp * 8.0 ).a );
			sh *= reveal;

			float glow = halo * 0.26 * ( 1.0 - sh * 0.92 ) + core * 1.1;
			float3 col = float3( glow, glow * 0.985, glow * 0.955 );

			// ---- the letters ---------------------------------------------
			float mask = tex2D( MapTexture, uv ).a;
			float lit  = 0.82 + 0.85 * exp( -pow( ( uv.x - lightX ) / 0.055, 2.0 ) );
			float3 letterCol = float3( 1.0, 1.0, 1.0 ) * min( lit, 1.55 );

			float la = mask * reveal;
			col = lerp( col, letterCol, la );

			col *= fade * Color.rgb;

			return float4( col, 1.0 );
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
	PixelShader = "PixelShaderTFRLoading"
}
Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderTFRLoading"
}
Effect Disable
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderTFRLoading"
}
Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderTFRLoading"
}
