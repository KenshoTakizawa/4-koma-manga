import React from 'react';
import { Menu } from "lucide-react"
import { cn } from "@/app/lib/utils"

interface MinediaLogoProps {
  className?: string
}

export const MinediaLogo: React.FC<MinediaLogoProps> = ({ className }) => {
  return (
    <div className={cn("flex items-center gap-4", className)}>
      {/* <Menu className="h-6 w-6 text-minedia-500" /> */}
      <span className="text-xl font-semibold text-minedia-500 pl-6">minediaマンガ</span>
    </div>
  )
}

