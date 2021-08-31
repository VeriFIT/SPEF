
typedef struct{
    int win_x;
    int win_y;
    int center_x;
    int center_y;

    int moves;
    int max_moves;
    int word_length;
    char guess_word[100];
    char current_word[100];
} game_state;


typedef struct word{
    char letter;
    struct word *next;
} word;






void print_empty_hangman(WINDOW *win);
void print_hangman_1(WINDOW *win);
void print_hangman_2(WINDOW *win);
void print_hangman_3(WINDOW *win);
void print_hangman_4(WINDOW *win);
void print_hangman_5(WINDOW *win);


void print_stats(WINDOW *win, int row, int col, int tries, int wrong, int max, char *used);
void print_at_line(WINDOW *win, int line, bool center, int col, const char *message);
void game_over_message(WINDOW *win, bool lose, int row, int col, char *mess);
bool guess_message(WINDOW *win, int row, int col, char *mess, char *used, bool show_all);

WINDOW *create_win(int width, int height, int center_x, int center_y);
void clear_win(WINDOW *win);
void destroy_win(WINDOW *win);

int process_input(char *mess);

void initProgram();
void quitProgram();
void updateScreen(game_state *gs);
void drawGuessWord();