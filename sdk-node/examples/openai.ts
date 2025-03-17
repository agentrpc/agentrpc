import { OpenAI } from "openai";
import { AgentRPC } from "../src";

const openai = new OpenAI({ apiKey: "" });
const agentrpc = new AgentRPC({ apiSecret: "" });


const main = async () => {
  const tools = await agentrpc.OpenAI.getTools();
    const completion = await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [
            {
                role: "user",
                content: "What is the weather in Melbourne?",
            },
        ],
        tools,
    });

    const message = completion.choices[0]?.message;

    if (message?.tool_calls) {
        for (const toolCall of message.tool_calls) {
            console.log("Agent is calling Tool", toolCall.function.name);
            const result = await agentrpc.OpenAI.executeTool(toolCall);
            console.log(result);
        }
    }
};

main();
