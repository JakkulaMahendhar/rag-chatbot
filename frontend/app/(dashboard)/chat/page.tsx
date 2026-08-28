"use client";

import { useEffect, useRef } from "react";
import { MessageSquarePlus, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { EmptyState } from "@/components/common/empty-state";
import { useChat } from "@/hooks/use-chat";

export default function ChatPage() {
  const { messages, isPending, sendMessage, startNewConversation } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isPending]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b px-6 py-3">
        <p className="text-sm font-medium">
          {messages.length > 0 ? "Conversation" : "New conversation"}
        </p>
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={startNewConversation}>
            <MessageSquarePlus className="size-4" />
            New chat
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-6">
          {messages.length === 0 ? (
            <EmptyState
              icon={Sparkles}
              title="Ask your knowledge base"
              description="Answers are generated from the documents you've uploaded - upload some first if you haven't."
            />
          ) : (
            messages.map((message) => <ChatMessage key={message.id} message={message} />)
          )}

          {isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="flex size-7 items-center justify-center rounded-full bg-secondary">
                <Sparkles className="size-3.5 animate-pulse" />
              </span>
              Thinking...
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t p-4">
        <div className="mx-auto w-full max-w-3xl">
          <ChatInput onSend={sendMessage} disabled={isPending} />
        </div>
      </div>
    </div>
  );
}
