-- Copyright (c) 2019 The DAML Authors. All rights reserved.
-- SPDX-License-Identifier: Apache-2.0
{-# LANGUAGE CPP             #-}
{-# LANGUAGE RecordWildCards #-}

import           Data.Version
import           Development.IDE.Main          (Command (..), commandP)


data GhcideArguments = GhcideArguments
    {argsCommand            :: Command
    ,argsShakeProfiling     :: Maybe FilePath
    -- them to just change the name of the exe and still work.
    , argsDebugOn           :: Bool
    , argsLogFile           :: Maybe String
    , argsThreads           :: Int
    , argsProjectGhcVersion :: Bool
    } deriving Show

data PrintVersion
  = PrintVersion
  | PrintNumericVersion
  deriving (Show, Eq, Ord)

data BiosAction
  = PrintCradleType
  deriving (Show, Eq, Ord)

printVersionParser :: String -> Parser PrintVersion
printVersionParser exeName =
  flag' PrintVersion
    (long "version" <> help ("Show " ++ exeName  ++ " and GHC versions"))
  <|>
  flag' PrintNumericVersion
    (long "numeric-version" <> help ("Show numeric version of " ++ exeName))

biosParser :: Parser BiosAction
biosParser =
  flag' PrintCradleType
    (long "print-cradle" <> help "Print the project cradle type")
    