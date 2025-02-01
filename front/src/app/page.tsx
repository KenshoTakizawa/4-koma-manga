"use client"

import { useState, useEffect } from "react"
import { Input } from "@/app/components/ui/input"
import { Button } from "@/app/components/ui/button"
import { Card, CardContent } from "@/app/components/ui/card"
import { Label } from "@/app/components/ui/label"
import Image from "next/image"
import { MinediaLogo } from "@/app/components/minedia-logo"

export default function Home() {
  const [messages, setMessages] = useState<string[]>([])
  const [productName, setProductName] = useState("")
  const [productDescription, setProductDescription] = useState("")
  const [showPanels, setShowPanels] = useState(false)
  const [imageUrls, setImageUrls] = useState<string[]>([])
  const [panelTexts, setPanelTexts] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (productName.trim() && productDescription.trim()) {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch("http://localhost:8080/generate_comic", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            product_name: productName,
            product_description: productDescription,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "API リクエストエラー");
        }

        const data = await response.json();

        setMessages([
          ...messages,
          `商品名: ${productName}`,
          `商品説明: ${productDescription}`,
          "システム: 4コマ漫画が生成されました",
        ]);

        setImageUrls(data.image_urls);
        setPanelTexts(data.texts);
        setShowPanels(true);

      } catch (error: any) {
        setError(error.message);
        console.error(error);
      } finally {
        setIsLoading(false);
      }
      setProductName("")
      setProductDescription("")
    }
  }

  // 画像の元のサイズ
  const originalWidth = 1024
  const originalHeight = 1024

  // 画像の新しいサイズ（3分の1）
  const newWidth = Math.round(originalWidth / 3)
  const newHeight = Math.round(originalHeight / 3)

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-minedia-50">
      <div className="z-10 max-w-md w-full items-center justify-between font-mono text-sm">
        <div className="fixed left-0 top-0 w-full border-b border-minedia-200 bg-white">
          <div className="container flex h-14 items-center">
            <MinediaLogo />
          </div>
        </div>

        <div className="mt-16">
          <Card className="mb-8 bg-white border-minedia-300">
            <CardContent className="p-6">
              {messages.map((msg, index) => (
                <p key={index} className="mb-2 text-minedia-800">
                  {msg}
                </p>
              ))}
            </CardContent>
          </Card>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4 mb-8">
            <div className="grid gap-2">
              <Label htmlFor="productName" className="text-minedia-800">
                商品名
              </Label>
              <Input
                id="productName"
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="例：さくらの香り柔軟剤"
                className="border-minedia-300 text-minedia-800 placeholder-minedia-400"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="productDescription" className="text-minedia-800">
                商品説明
              </Label>
              <Input
                id="productDescription"
                type="text"
                value={productDescription}
                onChange={(e) => setProductDescription(e.target.value)}
                placeholder="例：桜の香りが長時間続く、春限定の柔軟剤です"
                className="border-minedia-300 text-minedia-800 placeholder-minedia-400"
              />
            </div>
            <Button
              type="submit"
              className="bg-minedia-500 hover:bg-minedia-600 text-white w-full mt-2"
              disabled={!productName.trim() || !productDescription.trim() || isLoading}
            >
              {isLoading ? '生成中...' : 'マンガを生成'}
            </Button>
          </form>

          {error && <p className="text-red-500 mb-4">{error}</p>}

          {showPanels && (
            <div className="flex flex-col gap-4">
              {[0, 1, 2, 3].map((index) => (
                <Card key={index} className="w-full bg-white border-minedia-300">
                  <CardContent className="p-4 flex flex-col items-center">
                    {imageUrls[index] ? (
                      <Image
                        src={imageUrls[index]}
                        alt={`コマ${index + 1}`}
                        width={newWidth}
                        height={newHeight}
                        className="mb-2"
                      />
                    ) : (
                      <div className="animate-pulse w-[341px] h-[341px] bg-gray-200 rounded mb-2"></div>
                    )}
                    <p className="text-center font-bold mb-2 text-minedia-800">コマ{index + 1}</p>
                    <p className="text-sm text-center whitespace-pre-wrap text-minedia-700">{panelTexts[index]}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}