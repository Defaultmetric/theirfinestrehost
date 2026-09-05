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
			MipFilter = "None"
			AddressU = "Clamp"
			AddressV = "Clamp"
		}
	}
}

VertexStruct VS_OUTPUT
{
	float4 vPosition  : PDX_POSITION;
	float2 vTexCoord  : TEXCOORD0;
	float4 vScreenPos : TEXCOORD1;
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
			Out.vScreenPos = Out.vPosition;
			return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelShaderFlipbook
	[[
		// 112 frames of 512x288 packed 8 across, 14 down. Played at 14 fps
		// off the engine Time uniform, looping every 8 seconds.
		float4 main( VS_OUTPUT input ) : PDX_COLOR
		{
			const float COLS = 8.0;
			const float ROWS = 14.0;
			const float FRAMES = 112.0;

			// Looping frame index 0..111 (8 seconds loop at 14 fps)
			float f = floor( frac( abs( Time ) / 8.0 ) * FRAMES );
			float cy = floor( f / COLS );
			float cx = f - cy * COLS;

			// Screen-space position normalized to [0, 1] across entire viewport
			float w = max( abs( input.vScreenPos.w ), 0.00001 );
			float2 screenPos = input.vScreenPos.xy / w;

			float2 uvFrame;
			uvFrame.x = screenPos.x * 0.5 + 0.5;
			uvFrame.y = -screenPos.y * 0.5 + 0.5;

			// Preserve native 16:9 video aspect ratio across any monitor resolution (16:9, 16:10, 21:9)
			// WorldViewProjectionMatrix[0][0] is 2/ViewportWidth, [1][1] is 2/ViewportHeight
			float m00 = max( abs( WorldViewProjectionMatrix[0][0] ), 0.00001 );
			float m11 = max( abs( WorldViewProjectionMatrix[1][1] ), 0.00001 );
			float aspectScreen = m11 / m00;
			const float aspectVideo = 16.0 / 9.0;

			if ( aspectScreen > aspectVideo )
			{
				float s = aspectScreen / aspectVideo;
				uvFrame.y = ( uvFrame.y - 0.5 ) * s + 0.5;
			}
			else
			{
				float s = aspectVideo / aspectScreen;
				uvFrame.x = ( uvFrame.x - 0.5 ) * s + 0.5;
			}

			// Half-texel inset of a single 512x288 tile to prevent bilinear bleeding across atlas frames
			float2 halfTexel = float2( 0.5 / 512.0, 0.5 / 288.0 );
			float2 uvTile = clamp( uvFrame, halfTexel, 1.0 - halfTexel );

			// Map tile UV into the 8x14 texture atlas
			float2 uv = ( uvTile + float2( cx, cy ) ) / float2( COLS, ROWS );

			float4 OutColor = tex2D( MapTexture, uv );
			OutColor *= Color;
			return OutColor;
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
