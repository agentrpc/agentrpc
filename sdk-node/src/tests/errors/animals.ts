import { z } from "zod";
import { testInstance } from "../utils";

export const getNormalAnimal = async () => {
  throw new Error("This is a normal error");
};

export class AnimalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AnimalError";
  }
}

export const getCustomAnimal = async () => {
  throw new AnimalError("This is a custom error");
};

export const animalService = () => {
  const prefix = `animal${Math.random().toString(36).substring(2, 5)}`;
  const client = testInstance();

  client.register({
    name: `${prefix}_getNormalAnimal`,
    handler: getNormalAnimal,
    schema: {
      input: z.object({}),
    },
  });

  client.register({
    name: `${prefix}_getCustomAnimal`,
    handler: getCustomAnimal,
    schema: {
      input: z.object({}),
    },
  });

  return {
    client,
    prefix,
  };
};
