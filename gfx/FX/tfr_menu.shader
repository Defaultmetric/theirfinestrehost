# TFR main menu wordmark.
# On the first ~2s after the menu appears a light crosses the screen and
# reveals the letters. After that the letters stay lit and the light makes a
# slow pass every few seconds so the menu is not completely static.
Includes = {
	"tfr_menu.fxh"
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
	MainCode PixelShaderTFRMenu
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float2 uv = v.vTexCoord;

			// ---- intro sweep, driven by the age of the element ------------
			float age = Time - AnimationTime;
			float introLive = step( 0.0, age ) * step( age, TFR_INTRO_MAX );

			float sweepT = saturate( ( age - TFR_SWEEP_START ) / TFR_SWEEP_LEN );
			sweepT = sweepT * sweepT * ( 3.0 - 2.0 * sweepT );
			float introX = -0.22 + sweepT * 1.44;

			// ---- idle pass, driven by the global clock --------------------
			float ambT = saturate( frac( Time / TFR_AMBIENT ) * TFR_AMBIENT / 1.10 );
			ambT = ambT * ambT * ( 3.0 - 2.0 * ambT );
			float ambX = -0.22 + ambT * 1.44;

			// While the intro runs the light is the intro light and the
			// letters are hidden ahead of it. Otherwise they are always there.
			float useIntro = introLive * step( age, TFR_SWEEP_START + TFR_SWEEP_LEN + 0.35 );
			float lightX = lerp( ambX, introX, useIntro );
			float revealed = 1.0 - smoothstep( lightX - 0.015, lightX + 0.075, uv.x );
			float reveal = lerp( 1.0, revealed, useIntro );

			// ---- the bulb -------------------------------------------------
			float2 d = uv - float2( lightX, 0.5 );
			d.y *= TFR_QUAD_RATIO;
			float dist2 = dot( d, d );
			float halo = exp( -dist2 * 11.0 );
			float core = exp( -dist2 * 900.0 );

			// ---- shadows cast away from the bulb --------------------------
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

			float glow = halo * 0.24 * ( 1.0 - sh * 0.92 ) + core * 1.0;

			// ---- the letters ----------------------------------------------
			float mask = tex2D( MapTexture, uv ).a;
			float lit  = 0.86 + 0.80 * exp( -pow( ( uv.x - lightX ) / 0.055, 2.0 ) );
			float la   = mask * reveal;

			// Colour carries full brightness, alpha carries intensity, so the
			// glow does not get darkened twice when it blends over black.
			float3 col = lerp( float3( 1.0, 0.985, 0.955 ), float3( 1.0, 1.0, 1.0 ) * min( lit, 1.55 ), la );
			float  a   = saturate( max( glow, la ) );

			return float4( col * Color.rgb, a );
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}

Effect Up    { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRMenu" }
Effect Down  { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRMenu" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRMenu" }
Effect Over  { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRMenu" }
