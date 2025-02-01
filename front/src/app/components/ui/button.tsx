interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode
  }
  
  export function Button({ className, children, ...props }: ButtonProps) {
    return (
      <button
        className={`inline-flex items-center justify-center rounded-md px-4 py-2 font-medium ${className}`}
        {...props}
      >
        {children}
      </button>
    )
  }