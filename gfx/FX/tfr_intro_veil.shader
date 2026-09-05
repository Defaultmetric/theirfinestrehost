# Black curtain over the main menu for the first moment after it opens.
# Never goes fully opaque (0.94 max) on purpose: if the element age ever comes
# back pinned at zero, the worst case is a slightly dimmed but perfectly
# usable menu instead of a black screen you cannot get out of.
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
	MainCode PixelShaderTFRVeil
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			float age = Time - AnimationTime;

			// Only ever visible inside a short window right after the element
			// appears; anything outside that range means "no intro".
			float live = step( 0.0, age ) * step( age, TFR_INTRO_MAX );
			float a = ( 1.0 - smoothstep( 0.50, 1.30, age ) ) * live * 0.94;

			return float4( 0.0, 0.0, 0.0, a );
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}

Effect Up    { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRVeil" }
Effect Down  { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRVeil" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRVeil" }
Effect Over  { VertexShader = "VertexShader" PixelShader = "PixelShaderTFRVeil" }
