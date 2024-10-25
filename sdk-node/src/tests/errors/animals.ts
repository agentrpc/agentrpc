import { z } from "zod";
import { inferableInstance } from "../utils";

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

export const animalService = inferableInstance().service({
  name: "animal",
});

animalService.register({
  name: "getNormalAnimal",
  func: getNormalAnimal,
  schema: {
    input: z.object({}),
  },
});

animalService.register({
  name: "getCustomAnimal",
  func: getCustomAnimal,
  schema: {
    input: z.object({}),
  },
});
